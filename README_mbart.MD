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
FastAPI is designed to work with ASGI servers like Uvicorn. While FastAPI provides the framework for building APIs, Uvicorn is responsible for running the FastAPI application and handling incoming HTTP requests. In earlier attem I was trying to use forward end point though without success I was not able to give as argument source and target language to get around custom serving was prepared with translation endpoint<br> 
this is made by two files:<br>
custom_serving.py<br>
run_server.py<br>

(trans) u@u220:~/transformers/custom_server$ python run_server.py 

 ```
~/transformers/custom_server$ python run_server.py 
 
 ```
this was running in custom directory as follows to make it easy 
 
 
 ```
(trans) u@u220:~/transformers/custom_server$ python run_server.py 
INFO:     Started server process [9693]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8888 (Press CTRL+C to quit)
 ``` 

small explanation to POST content
 ```
"http://localhost:8888/translate?inputs=Hello,%20how%20are%20you?%20good.%20And%20you?&src_lang=en_XX&tgt_lang=hi_IN"
 ```
%20 is just space representation <br>
rc_lang=en_XX&tgt_lang=hi_IN is giving source and target language according to<br>
langs=ar_AR,cs_CZ,de_DE,en_XX,es_XX,et_EE,fi_FI,fr_XX,gu_IN,hi_IN,it_IT,ja_XX,kk_KZ,ko_KR,lt_LT,lv_LV,my_MM,ne_NP,nl_XX,ro_RO,ru_RU,si_LK,tr_TR,vi_VN,zh_CN<br>

and the answer(in Hindu) was

 ```
curl -X POST      -H "Content-Type: application/json"      "http://localhost:8888/translate?inputs=Hello,%20how%20are%20you?%20good.%20And%20you?&src_lang=en_XX&tgt_lang=hi_IN" |
jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   130  100   130    0     0     15      0  0:00:08  0:00:08 --:--:--    32
{
  "translation": [
    {
      "translation_text": "नमस्ते, आप कैसे हैं? अच्छा है. और आप?"
    }
  ]
}


 ```


Then next step was dockerising whole process so it will be easy transferable
I did that on alpine docker LXC in proxmox 
 Dockerfile was prepared and image created

 Dockerfile content is :

```
# Use a lightweight Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the required files
COPY custom_serving.py run_server.py ./

# Install the required dependencies
RUN pip install --no-cache-dir \
    transformers[serving] \
    torch \
    sentencepiece \
    protobuf  \
    && python -c "from transformers import pipeline; pipeline('translation', model='facebook/mbart-large-50-many-to-many-mmt')" \
    && rm -rf /root/.cache/pip

# Expose the port for the server
EXPOSE 8888

# Set the entry point
CMD ["python", "run_server.py"]


 ```


image could be build locally or on remote machine/remote LXC container in Promox  ( I used ssh and scp to that machine to copy there Docckerfile as above this time) just not to polute my ubuntu environment
with large docker images.
 ```
docker build -t mbart-translation-server
 ```

and then started

```
docker run -it  --rm -p 7001:8888  mbart-translation-server
```
port mapping was done so the translation service will be visible outside of the docker

as this time translation is done on other machine POST is a bit different ging IP of that machine
```
curl -X POST      -H "Content-Type: application/json"      "http://192.168.xx.102:7001/translate?inputs=Hello,%20how%20are%20you?%20good.%20And%20you?&src_lang=en_XX&tgt_lang=de_DE" |jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    74  100    74    0     0     12      0  0:00:06  0:00:05  0:00:01    19
{
  "translation": [
    {
      "translation_text": "Hallo, wie geht es? gut. Und Sie?"
    }
  ]
}
u@u220:~$ curl -X POST      -H "Content-Type: application/json"      "http://192.168.xx.102:7001/translate?inputs=Hello,%20how%20are%20you?%20good.%20And%20you?&src_lang=en_XX&tgt_lang=ar_AR" |jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    93  100    93    0     0     16      0  0:00:05  0:00:05 --:--:--    21
{
  "translation": [
    {
      "translation_text": "مرحباً، كيف حالك؟ جيد. و أنت؟"
    }
  ]
}

```
![](mbart.gif)

## 2 How to make  mbart translating in bulk ( book or pdf file)
Once again I will use  docker this time python script will load pdf file from current directory split that to sentencies ,
translate each sentence to given language according to initial setup and save them in two txt files one where there both source and target language and second where there is only target language. this will be done by docker image this second imaage will be responsible for loading pdf spliting that to sentencies sending request to previous uvicorn fast server receive response and save that to file.
Dockerfile is as follows
 ```
FROM python:3.9-slim

# Install required libraries
RUN pip install --no-cache-dir pymupdf requests && \
    pip install PyPDF2

# Copy the Python script
COPY translate_pdf.py /app/translate_pdf.py

# Set the working directory
WORKDIR /app

# Set the entry point
ENTRYPOINT ["python", "/app/translate_pdf.py"]


 ```
image is created with command:

```
docker build -t pdf-translator .

```
and running it in directory where there is odf to translate

```

docker run -it --rm -v "${PWD}:/tmp/pdf_translator" pdf-translator
```

### Status
Project is: _in progress_ 
