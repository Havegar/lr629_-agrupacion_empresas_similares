#!/usr/bin/env python
# coding: utf-8

# ## Apiux & SII: Analisis exploratorio de datos y depuracion de data sociedades
# ## ATENCION: proyecto sujeto a mantenimiento continuo. 
# 
# ## Henry Vega (henrry.vega@api-ux.com)
# ## Data analyst

# In[1]:


from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark import SparkContext, SparkConf
import pyspark
import pandas as pd
#warnings.filterwarnings('ignore', category=DeprecationWarning)


# In[2]:


spark = SparkSession.builder \
  .appName("Test")  \
  .config("spark.yarn.access.hadoopFileSystems","abfs://data@datalakesii.dfs.core.windows.net/") \
  .config("spark.executor.memory", "16g") \
  .config("spark.driver.memory", "12g")\
  .config("spark.executor.cores", "2") \
  .config("spark.executor.instances", "10") \
  .config("spark.driver.maxResultSize", "12g") \
  .getOrCreate()


# ## Carga de relaciones societarias y depuracion de data

# Primero, veamos los valores null en participacion de capital y participacion de utilidades.

# In[3]:


spark.sql("select RUT_SOCIEDAD, RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES from libsdf.jab_soc_2023_inom where PORCENTAJE_CAPITAL is null or PORCENTAJE_UTILIDADES IS NULL").show()


# Vemos que no hay valores nulos en la tabla. A continuacion veamos cuantos duplicados existen en las columnas de interes:
# RUT_SOCIEDAD,RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES, pues todos
# los calculos lo haremos basados en esta columnas.

# In[4]:


spark.sql("select * from libsdf.jab_soc_2023_inom where RUT_SOCIEDAD like 'dwElNqcCQQiFyI3ic%' ").show()


# In[5]:


spark.sql("select RUT_SOCIEDAD, RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES, count(*) as c from libsdf.jab_soc_2023_inom  group by  RUT_SOCIEDAD, RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES order by c desc").createOrReplaceTempView("sociedad")
spark.sql("select * from sociedad").show()
spark.sql("select RUT_SOCIEDAD, RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES from sociedad").createOrReplaceTempView("sociedad")


# Donde seleccionamos los valores no repetidos. Haciendo nuevamente un recuento de los valores unicos,

# In[6]:


spark.sql("select RUT_SOCIEDAD, RUT_SOCIO, count(*) as count from sociedad group by RUT_SOCIEDAD, RUT_SOCIO order by count desc ").show()


# Por lo visto tenemos unicidad de la relaciones sociedad socio, a juzgar por el recuento de las combinaciones. Ahora veremos cuanto suman los valores de PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES para cada una de las sociedades.
# 

# In[7]:


spark.sql("select RUT_SOCIEDAD, SUM(PORCENTAJE_CAPITAL) as CAPITAL,SUM(PORCENTAJE_UTILIDADES) as UTILIDADES from sociedad group by RUT_SOCIEDAD order by CAPITAL DESC").show()


# In[8]:


spark.sql("select RUT_SOCIEDAD, SUM(PORCENTAJE_CAPITAL) as CAPITAL,SUM(PORCENTAJE_UTILIDADES) as UTILIDADES from sociedad group by RUT_SOCIEDAD order by CAPITAL ASC").show()


# In[9]:


# Ahora vamos las entradas con al menos un valor cero (que indica cero participacion porcentual)

# In[10]:


spark.sql("select COUNT(*) from sociedad WHERE PORCENTAJE_CAPITAL=0 OR PORCENTAJE_UTILIDADES=0").show()


# Por lo visto, tenemos 1057765 entradas donde al menos uno de ambos porcentajes es cero. Por otro lado, tenemos 
# 1053936 registros donde ambos porcentajes son cero.
# 

# Ahora veamos cuales porcentajes de capital son cero y luego los porcentajes de utilidades son cero.



# Para el analisis del problema de oscuridad, es mejor tener en cuenta los porcentajes de participacion de capital, porque los creditos se reparten segun la participacion societaria.
# Ahora veamos cuantos tienen valores positivos mayores que 100 o negativos.

# In[12]:


# El cual es solo un valor levemente superior a 100 %. Seleccionamos los que no tienen valores cero en PORCENTAJE_CAPITAL.
# IMPORTANTE: de ser utilizado PORCENTAJE_UTILIDADES se debe filtrar sobre esa columna.

# In[13]:


spark.sql("select * from sociedad where PORCENTAJE_CAPITAL!=0").createOrReplaceTempView("sociedad")


# In[14]:



# In[15]:


sociedad=spark.sql("select * from sociedad").toPandas()
sociedad.to_csv('/home/cdsw/data/processed/malla_societaria/sociedades_participacion_capital_nozero.csv', index=False)

