FROM jupyter/pyspark-notebook:spark-3.5.0

RUN pip install --quiet pyspark==3.5.0 pytest>=8.0.0

COPY solution.ipynb /home/jovyan/solution.ipynb
COPY app/ /home/jovyan/app/
