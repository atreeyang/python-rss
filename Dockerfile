FROM daocloud.io/python:3-onbuild
EXPOSE 5000
CMD [ "python", "./runserver.py" ]
