'''
License
-------
Written by Andre Panisson
Copyright (c) 2011 Andre Panisson <panisson@gmail.com>
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
'''

import urllib2
import json

class JSONClient(object):
    
    def __init__(self, url='http://127.0.0.1:8080/workspace0', autoflush=False):
        self.url = url
        self.data = ""
        self.autoflush = autoflush
        
    def flush(self):
        if len(self.data) > 0:
            self.__send(self.data)
            self.data = ""
        
    def __send(self, data):
        conn = urllib2.urlopen(self.url + '?operation=updateGraph', data)
        return conn.read()
        
    def add_node(self, id, flush=True, **attributes):
        self.data += json.dumps({"an":{id:attributes}}) + '\r\n'
        if(self.autoflush): self.flush()
    
    def delete_node(self, id):
        self.__send(json.dumps({"dn":{id:{}}}))
    
    def add_edge(self, id, source, target, directed=True, **attributes):
        attributes['source'] = source
        attributes['target'] = target
        attributes['directed'] = directed
        self.data += json.dumps({"ae":{id:attributes}}) + '\r\n'
        if(self.autoflush): self.flush()
    
    def delete_edge(self, id):
        self.__send(json.dumps({"de":{id:{}}}))
        
    def clean(self):
        self.__send(json.dumps({"dn":{"filter":"ALL"}}))

