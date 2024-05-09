## 1 How mBart50 transformer meets docker 

> <p>How quickly with the use of cli on ubuntu machine get translation.<br>
In this example I use multilingual mBart facebook/mbart-large-50-many-to-many-mmt
transformers library fron HuggingFace jq( to decipher jason)  and curl  just to present how to 
using cli based tools get things done
installing libraries

To avoid poluting ubuntu everything will be done in virtual environment (trans)
ubuntu  is virtual machine on Proxmox for convenience.

 ```
python3 -m venv trans
source trans/bin/activate
 ``` 
 and required libraries:

 ```
 pip install --no-cache-dir torch && \
 pip install --no-cache-dir transformers[serving] && \
 pip install --no-cache-dir sentencepiece && \
 pip install jq && \
 pip install protobuf
 
 ```
transformers[serving] will install in package FastAPI and Uvicorn  included so we can have interface.
FastAPI is designed to work with ASGI servers like Uvicorn. While FastAPI provides the framework for building APIs, Uvicorn is responsible for running the FastAPI application and handling incoming HTTP requests. 
Once everything is installed lets execute translation task

 ```
transformers-cli serve   --task translation   --host 0.0.0.0   --port 8000   --model Helsinki-NLP opus-mt-es-de   --tokenizer Helsinki-NLP/opus-mt-es-de   --device -1
 
 ```
.
 
 
 ```
curl -X POST   http://0.0.0.0:8000/forward   -H "Content-Type: application/json"   -d '{
    "inputs": "Yo no soy sorprendido  que es possible hacer una traduccion desde una idioma a otra con transformers-cli",
    "parameters": {
      "src_lang": "es",
      "tgt_lang": "de"
    }
  }' | jq
 ``` 
and the answer was


 ```
  curl -X POST   http://0.0.0.0:8000/forward   -H "Content-Type: application/json"   -d '{
    "inputs": "Yo no soy sorprendido  que es possible hacer una traduccion desde una idioma a otra con transformers-cli",
    "parameters": {
      "src_lang": "es",
      "tgt_lang": "de"
    }
  }' 
{"output":[{"translation_text":"Ich bin nicht überrascht, dass es möglich ist, eine Übersetzung von einer Sprache in eine andere mit transformers-cli zu machen."}]}root@pve:~# 


 ```


Then next step was dockerising whole process so it will be easy transferable
I did that on alpine docker LXC in proxmox 
 Dockerfile was prepared and image created

 Dockerfile content is :

```
# Use a minimal base image
FROM python:3.9-slim-buster

# Set working directory
WORKDIR /app

# Install transformers library
RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch && \
    pip install --no-cache-dir transformers[serving] && \
    pip install --no-cache-dir sentencepiece && \
    pip install jq && \
    pip install protobuf



# Clean up
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 8888
# Define entry point
ENTRYPOINT ["transformers-cli",  "serve",  "--port=8888", "--host=0.0.0.0", "--task=translation", "--model=Helsinki-NLP/opus-mt-es-de", "--tokenizer=Helsinki-NLP/opus-mt-es-de"]

 ```
As you see the same content but placed together

image could be build( here the name "mara:04") with CLI or portainer builder
and then started

```
docker run -it  --rm -P mara:04
```

![](mbart.gif)
### Status
Project is: _in progress_ 