
#!/bin/bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker Fancy_crawling:app
