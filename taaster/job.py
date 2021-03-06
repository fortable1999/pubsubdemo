#!/usr/bin/env python

"""
job.py
Mixin for Abstract Tester

Descript how job processed detaily.
"""

import asyncio
import aiohttp
import asyncssh
import kafka
import sys
import json
import base64

from taaster.log import BaseLoggingMixin

class BaseJobMixin(BaseLoggingMixin):
    job_id = None
    job = None


class CouchDBJobStorageMixin(BaseJobMixin):
    couchdb_host = "localhost"
    couchdb_port = 8081

    def get_job_query(self):
        return "http://%s:%d/v1/log" % (self.couchdb_host, self.couchdb_port)

    async def get_job(self, job_id):
        response = await aiohttp.request("GET", self.get_job_query()+"/"+job_id)
        chunk = await response.content.read()
        response.close()
        return json.loads(chunk.decode('utf-8'))

    async def put_job(self, job_id, doc):
        body = base64.b64encode(bytes(json.dumps(doc), 'utf-8'))
        response = await aiohttp.request("POST", self.get_job_query(), data=body)
        chunk = await response.content.read()
        response.close()
        return json.loads(chunk.decode('utf-8'))


class SSHJobMixin(BaseJobMixin):
    async def do_ssh_job(self, 
            host, 
            port, 
            username, 
            password, 
            cmd_list, 
            async_callback=None, 
            async_err_callback=None, 
            async_finish_callback=None, 
            *args, **kwargs):
        try:
            with await asyncssh.connect(
                    host, 
                    port=port, 
                    username=username, 
                    password=password, 
                    known_hosts=None, 
                    client_keys=[]
                    ) as conn:
                for cmd in cmd_list:
                    self.logger.info("$ %s" % cmd)
                    stdin, stdout, stderr = await conn.open_session(cmd)
                    output = await stdout.read()
                    output_error = await stderr.read()
                    status = stdout.channel.get_exit_status()
                    if status:
                        self.logger.info("Script finished with %d. Stop." % status)
                        if async_callback:
                            await async_callback(output)
                        if async_err_callback:
                            await async_err_callback(output_error)
                        if async_finish_callback:
                            await async_finish_callback("TaaS worker failed")
                        return
                    else:
                        if async_callback:
                            await async_callback(output)
            if async_finish_callback:
                await async_finish_callback("TaaS worker success")
        except OSError as e:
            if async_err_callback:
                await async_err_callback("TaaS worker error: %s" % e)
            if async_finish_callback:
                await async_finish_callback("TaaS worker finished")


class CurlJobMixin(BaseJobMixin):
    async def do_curl_job(self, url, method="GET", **kwargs):
        response = await aiohttp.request("GET", url)
        chunk = await response.content.read()
        response.close()
        return chunk.decode('utf-8')


class KafkaWriteJobMixin(BaseJobMixin):
    def do_kafka_write_job(self, *args, **kwargs):
        producer = kafka.SimpleProducer(kafka, async=True)
        producer.send_messages(b'my-topic', b'async message')

if __name__ == '__main__':
    import functools

    class SSHTest(SSHJobMixin):
        pass

    async def printitout(data):
        
        print(">>> Test callback")
        print(data)
        print("<<<")
            
    ssh = SSHTest()
    asyncio.get_event_loop().run_until_complete(ssh.do_ssh_job(
        "localhost",
        "2222",
        "vagrant",
        "vagrant",
        ["whoami", "whoami", "whereis python"],
        async_callback=functools.partial(printitout),
        async_err_callback=functools.partial(printitout),
        async_finish_callback=functools.partial(printitout),
        ))
