## Tabla de contenidos
1. [General Info](#general-info)
2. [Tecnologias](#Tecnologias)
3. [Recursos CML](#Recursos_CML)
4. [Colaboradores](#Colaboradores)
5. [Instalación](#Instalación)
6. [Ejecución](#Ejecución)
7. [Explicación](#Explicación)
8. [Sugerencias y pasos siguientes](#Sugerencias)
9. [Estructura de carpetas](#plantilla_proyectos_python)
10. [Estructura de tablas y rutas](#Estructura_rutas_tablas)

# Proyecto de Análisis de Grupos Económicos

## Información General

Este proyecto tiene dos partes, en primer lugar un estudio de las características de grupos económicos conocidos junto al flujo de IVA de estos grupos en base a sus relaciones comerciales, en segundo lugar un esfuerzo por identificar grupos economicos con bases a un grafo que contiene nodos, correspondinentes a personas naturales o juridicas y relaciones entre ellos, de diverso tipo. El objetivo principal de esta segunda parte es identificar y analizar estas relaciones y peso respectivo que permita maximizar la similitud con los grupos economicos definidos por expertos. 

En particular, este proyecto se centra en las siguientes relaciones:

- **Relaciones Societarias**: Vínculos entre empresas y sus accionistas (con peso de participación societaria).
- **Relaciones de Representantes Legales**: Conexiones entre entidades y sus representantes legales.
- **Relaciones de Contador**: Asociaciones basadas en los contadores que gestionan las cuentas de múltiples entidades.
- **Relaciones Familiares**: Vínculos familiares, específicamente relaciones de cónyuge e hijos, que pueden involucrar a personas que sean representantes, socios, contadores, o estén fuera de estas categorías. Se escogio solo este par de tipos de relaciones pues son las que generan conexion principal en las familias y por el excesivo volumen de datos al escoger mas tipos.
- 
Cada tipo de relación tiene un peso específico en el análisis, por lo cual se construira un gridsearch que permita maximizar la similitud buscada. Esta metodología no solo ayuda a comprender mejor las dinámicas internas de los grupos económicos, sino que también proporciona una herramienta útil para la evaluación y de entidades desde una perspectiva tributaria y financiera. Para ello es necesario incluir los dos siguientes conceptos que seran claves para comprender las caracteristicas de este proyecto:

### Algoritmo de Louvain para la Detección de Comunidades:

El algoritmo de Louvain es un método eficiente y popular para detectar comunidades en redes. Funciona de la siguiente manera básica.

1. **Fase de Optimización Local:**
   - Inicialmente, cada nodo se coloca en su propia comunidad.
   - Luego, de manera iterativa, se evalúa la ganancia en modularidad que se obtendría al mover un nodo a la comunidad de uno de sus vecinos. Si la ganancia es positiva, se realiza dicho movimiento.
   - Este proceso se repite hasta que no se pueda obtener más ganancia en modularidad mediante movimientos locales.

2. **Fase de Agregación y Repetición:**
   - Después de la fase de optimización local, se procede a formar una nueva red donde los nodos representan las comunidades encontradas en la fase anterior.
   - Se repite el proceso de optimización local en esta nueva red agregada hasta que no se pueda mejorar más la modularidad.

3. **Resultados:**
   - Al finalizar, el algoritmo devuelve las comunidades encontradas en forma de una partición de la red original, maximizando la modularidad, que es una medida de la calidad de la partición en términos de la densidad de conexiones dentro de las comunidades y la escasez de conexiones entre ellas.

El algoritmo de Louvain es popular debido a su capacidad para manejar grandes redes eficientemente y por producir particiones de alta calidad en términos de modularidad. 

### Índice de Ajuste Mutuo para Comparar Comunidades:

El índice de ajuste mutuo es una medida utilizada para comparar la similitud entre dos particiones diferentes de un conjunto de elementos, como comunidades encontradas por diferentes métodos o comunidades teóricas.

- **Definición:**
    - El índice de ajuste mutuo mide la similitud entre dos particiones considerando las relaciones entre los pares de elementos que caen en la misma comunidad en ambas particiones, ajustado por azar.

- **Utilidad en Comparación de Comunidades:**
    - *Comunidades Ficticias vs. Encontradas:* Permite comparar cómo de similar son las comunidades encontradas por el algoritmo de Louvain con comunidades generadas aleatoriamente (ficticias). Un alto índice de ajuste mutuo indica que las comunidades encontradas son significativamente similares a las esperadas por azar, mientras que un bajo índice indica una estructura de comunidad más distintiva y no aleatoria.

- **Interpretación:**
    - Proporciona una medida cuantitativa de la calidad y la coherencia de las comunidades detectadas por el algoritmo de Louvain en comparación con las expectativas de agrupamiento aleatorio, ayudando a validar la estructura comunitaria encontrada en la red analizada.

## Tecnologías Utilizadas

### Apache Spark
- *Versión*: 3.2.3
- *Uso*: Consulta de tablas ubicadas en el Data Lake.
- *Configuración*:
  - Memoria de ejecución: 16 GB
  - Memoria del driver: 12 GB
  - Núcleos de ejecución: 2
  - Instancias de ejecución: 2

### Python
- *Versión*: 3.10
- *Uso*: Procesamiento adicional en Cloudera Machine Learning (CML).
- *Tipo de sesi*: Por otro lado y acerca de la ejecución del proyecto, se requiere en particular que las sesiones de trabajo tengan una memoria ram de 96 gb y 7 CPU como mínimo.


### Packages de Python mas utilizados
- *pandas*: Manejo de dataframes
- *numpy*: Operaciones matematicas
- *pyspark*: Para interactuar con Spark desde Python.
- *community*: Implementación de algoritmos de detección de comunidades.
- *seaborn*: Visualización de datos.
- *matplotlib*: Generación de gráficos y visualizaciones.
- *warnings*: Gestión de mensajes de advertencia.
- *json*: Manipulación de datos en formato JSON.
- *os*: Interacción con el sistema operativo.
- *NetworkX*: Análisis y visualización de redes complejas.
- *igraph*: Análisis de grafos y redes.
- *Scikit-learn (sklearn)*: Métricas y herramientas para el análisis de datos.
- *leidenalg*: Ejecuta el algoritmo de Leiden.

### Spark y Python en la Caracterización de Grupos Económicos
- *Uso*: Consulta y análisis de tablas para identificar características de los grupos económicos conocidos y realizar tanto el analisis de datos como los calculos correspondientes.

## Descripción de los Recursos CML Utilizados en el Proyecto

#### Primera Parte: Análisis del Grupo Económico y Propiedades Principales

#### 1. Análisis de Grupos Económicos y flujo de IVA:
  - Utilización de dos notebooks para realizar un análisis exhaustivo de las propiedades de los grupos económicos y del flujo de IVA intra y extragrupo.
  -  Definición de dos notebooks adicionales para procesos de preprocesamiento de datos y un script utilizado para la depuración de las sociedades. Se detallaran mas adelante.

### Segunda Parte: procesos de Partición de Entidades Tributarias

#### 1. Obtención de datos y creacion de grafos:
   -  Ejecución de varios archivos ejecutables que agregan capas de relaciones a un grafo construido sin pesos de relacion, ejecutan el algoritmo de Louvain y que permite obtener los datos con la particion correspondiente.
   -  Procedimientos automatizados de extracción, transformación y carga (ETL) para consolidar y almacenar los datos. El grafo se construye a partir de diferentes capas de relaciones sin peso.
   -  Se ejecutaron varios ejecutables en jobs con el grafo completo a partir de capas de relaciones que se iban sumando, sin peso, unas sobre otras en el proceso de creacion del grafo.

#### 2. Partición del Subgrafo y ejecucion final (considerando pesos de relaciones):
   - **Cálculo de Subgrafo:** Ejecución de un archivo .py en un job para calcular el subgrafo inicial.
   - **Grid Search:** Ejecución de otro archivo .py para realizar el Grid Search basado en la centralidad de los nodos, enfocándose en el top 10% con mayor centralidad. Inicialmente se investigo con una muestra aleatoria de datos basado en representatividad de nodos y relaciones, lo cual resulto insatisfactorio en performance por el bajo Indice de Ajuste Mutuo de la muestra. 
   - **Ejecución final:** Uso de los valores óptimos obtenidos del Grid Search en el grafo completo para ejecutar el algoritmo de partición final.
     
## Resumen del Flujo de Trabajo

El resumen del flujo de trabajo, de forma muy general se menciona a continuacion.

1. **Análisis de  Grupos Económicos:**
En un notebook, **Analisis cuantitativo de grupos economicos.ipynb** se realizara un análisis detallado de las caracteristicas de personas juridicas pertenecientes a diferentes grupos economicos, definidos previamente por criterio experto. Las caracteristicas a analizar son las siguientes:
  - Familiaridad (calculada en proyectos anteriores)
  - Oscuridad (calculada en proyectos anteriores)
  - Contadores de la sociedad
  - Representantes legales
  - Direcciones
  - Correos
  - Patrimonio empresarial (calculo realizado con iteraciones de patrimonios naturales en malla societaria.)
  - Rubro y sub Rubro de cada empresa
  - Directores (informacion obtenible a partir de formulario 29)
  - Trabajadores (informacion obtenidaa partir de proyectos anteriores)
  - Lugares de Venta y si distribuye o no a zonas extremas del pais.
  - 
En un siguiente notebook, **IVA_grupos_economicos.ipynb** se realiza un analisis del flujo de IVA de estos grupos economicos, donde se calculan los siguientes datos agregados:
  - Numero de contribuyentes
  - Porcentaje de IVA recepcion extragrup
  - Recepcion IVA extragrupo
  - Porcentaje de IVA emision extragrupo 
  - Emision intragrupo
  - Emision_extragrupo 
  - Tasa de emision intra y extragrupo
  
Se obtienen subproductos del calculo de las caracteristicas asociados a estos grupos economicos, tales como el patrimonio societario, o bien los datos de emision y recepcion de IVA por grupo. Estos detalles se indicaran mas adelante.

2. **Partición de Entidades Tributarias:**
  - Se procesa,  obtiene y almacena la data de relaciones entre entidades de tipo societario, representante, contador y familiar (hijo/conyuge).
   - Se realizan diferentes procesos de construccion de grafos sin pesos, con toda la data para analizar performance. 
   - Se construye un grafo y se extrae un subgrafo representativo con el 10 % de los datos con el objetivo de hacer un gridsearch con el peso relativo de las relaciones para este grafo no dirigido. 
   - Se ejecutan particiones del subgrafo utilizando el algoritmo de Louvain. Inicialmente se habia tambien contemplado el algoritmo de  Leiden, con las decision correspondiente de no utilizar finalmente este ultimo por la baje performance del mismo.


## Colaboradores
***
En este proyecto participa Henry Vega, Data Analyst de APIUX asi como el equipo del Área de Riesgo e Informalidad del SII, compuesto por Daniel Cantillana, Jorge Bravo y Yasser Nanjari, además Arnol Garcia, jefe de área y Manuel Barrientos, con soporte técnico en el espacio de trabajo y Jorge Estéfane, jefe de proyecto por parte de APIUX.

## Instalacion
***
Los pasos para instalar el proyecto y sus configuraciones en un entorno nuevo en caso que sea necesario, por ejemplo:
1. Instalar paquetes
  - Ingresar a la carpeta package_requeriment y abrir la terminal 
  - Escribir el siguiente comando: pip install -r requirements.txt
2. Ejecutar Notebooks (analisis de grupos economicos y/o busqueda de grupos economicos) y scripts en sus jobs respectivos.
3. Uso posterior de la data output obtenida. 

## Ejecucion del proyecto
************************************************
### Primera parte: analisis de grupos economicos

#### Procesamiento de Datos
Esta sección proporciona una guía sobre cómo ejecutar el procesamiento de datos necesario para llegar a los productos finales, que son los notebooks de análisis de grupos económicos y el análisis de IVA de estos grupos.
El proyecto incluye varios scripts y notebooks en la carpeta src/.data que deben ejecutarse.

1. Cantidad de Trabajadores (**scr/data/Cantidad de Trabajadores.ipynb**): •Este notebook procesa la información sobre la malla societaria depurada para obtener el número de trabajadores a honorarios y contratados en cada empresa a partir de la ultima declaracion. Los resultados se utilizan posteriormente en el análisis de los grupos económicos. El archivo de salida se guarda en **/data/processed/trabajadores/trabajadores_last_declaration.csv**.

2. Depuración de Sociedades (**scr/data/depuracion_sociedades.py**): • Este script depura los datos relacionados con la estructura de la malla societaria y sus pesos y valores. Es esencial para limpiar y preparar los datos antes de su análisis. El archivo de salida se guarda en **/data/processed/malla_societaria/sociedades_participacion_capital_nozero.csv**

3. Propagación de patrimonio (**scr/data/propagacion_patrimonio.ipynb**): • Utiliza la malla societaria para propagar patrimonio  a través de los pesos de la malla societaria y determinar cuánto capital podría tener una empresa respecto a sus socios. Este proceso involucra un algoritmo iterativo sobre la participación societaria. Genera un archivo que se guarda en formato parquet en **abfs://data@datalakesii.dfs.core.windows.net/DatoOrigen/lr-629/Agrupacion_empresas_similares/patrimonio/patrimonios_completos**.

####  Análisis de datos 

Después de procesar los datos, se procede al análisis de los grupos económicos utilizando los notebooks ubicados en la carpeta base del proyecto (notebooks):

1. Análisis Cuantitativo de Grupos Económicos (**notebooks/Analisis cuantitativo de grupos economicos.ipynb**): • Este notebook realiza un análisis detallado de los grupos económicos utilizando las características derivadas del procesamiento de datos previo.
2. Análisis de IVA de Grupos Económicos (**notebooks/IVA_grupos_economicos.ipynb**): •Este notebook se centra en el flujo de IVA dentro de los grupos económicos, proporcionando una visión sobre el flujo de IVA hacia y desde esos grupos.Ademas consolida la data en **/home/cdsw/data/processed/iva_grupos_economicos/iva_grupos_economicos.csv**
**********************************************************

### Segunda parte: Búsqueda de Comunidades

Esta sección se enfoca en la búsqueda de comunidades dentro de los grupos económicos. Se divide en dos partes: una sin optimización y la otra con optimización y pesos.

#### Ejecucion sin Optimización

En esta primera parte, se ejecutaron una serie de scripts para construir el grafo completo con todas las relaciones, pero sin considerar pesos. A través de diferentes combinaciones de estas capas, se buscó determinar las particiones del grafo. Cada uno de estos notebooks genera un archivo de salida con una clasificación de Louvain para cada configuración.

Los scripts utilizados son los siguientes:

1. **scr/models/previo/Algoritmo_louvain_malla_societaria.py**
    - Este script permite construir el grafo completo de entidades considerando solo las relaciones societarias, sin asignar pesos a estas relaciones.
    - El archivo de salida contiene una clasificación de Louvain para todas las entidades que son nodos del grafo, este se encuentra en **'/home/cdsw/data/processed/louvain_malla_societaria/louvain_malla_societaria.csv'** junto a un dataset con valores de modularidad vs resolucion en el calculo de la particion del grafo **data/processed/louvain_malla_societaria/resolucion_modularidad.csv**. Esta ultima data tambien es desplegada graficamente en la ejecucion de este script.
   
2. **scr/models/previo/Algoritmo_louvain_malla_societaria_contadores.py**
    - Este script permite construir el grafo completo de entidades considerando las relaciones societarias y tambien las de contadores, sin asignar pesos a estas relaciones.
    - El archivo de salida contiene una clasificación de Louvain para todas las entidades que son nodos del grafo, este se encuentra en **/data/processed/louvain_malla_societaria_contador/louvain_malla_societaria_contador.csv** junto a un dataset con valores de modularidad vs resolucion en el calculo de la particion del grafo **/data/processed/louvain_malla_societaria_contador/resolucion_modularidad.csv**. Esta ultima data tambien es desplegada graficamente en la ejecucion de este script.
   
3. **scr/models/previo/Algoritmo_louvain_malla_societaria_contadores_representante.py**
    - Este script permite construir el grafo completo de entidades considerando las relaciones societarias y tambien las de contadores y representantes legales, sin asignar pesos a estas relaciones.
    - El archivo de salida contiene una clasificación de Louvain para todas las entidades que son nodos del grafo, este se encuentra en **/data/processed/louvain_malla_societaria_contador_representante/louvain_malla_societaria_contador_representante.csv** junto a un dataset con valores de modularidad vs resolucion en el calculo de la particion del grafo **/data/processed/louvain_malla_societaria_contador_representante/resolucion_modularidad.csv**. Esta ultima data tambien es desplegada graficamente en la ejecucion de este script.
   
4. **scr/models/previo/Algoritmo_louvain_malla_societaria_contadores_representante_familiares.py**
    - Este script permite construir el grafo completo de entidades considerando las relaciones societarias y tambien las de contadores,representantes legales y familiares (hijo y conyuge), sin asignar pesos a estas relaciones.
    - El archivo de salida contiene una clasificación de Louvain para todas las entidades que son nodos del grafo, este se encuentra en **/data/processed/louvain_malla_societaria_contador_representante_familiares/louvain_malla_societaria_contador_representante_familiares.csv** junto a un dataset con valores de modularidad vs resolucion en el calculo de la particion del grafo **/data/processed/louvain_malla_societaria_contador_representante_familiares/resolucion_modularidad.csv**. Esta ultima data tambien es desplegada graficamente en la ejecucion de este script.
   
5. **scr/models/previo/Algoritmo_louvain_malla_societaria_pesos.py**
    - Este script permite construir el grafo completo de entidades considerando las relaciones societarias y asignando pesos a estas relaciones que corresponde a su participacion societaria.
    - El archivo de salida contiene una clasificación de Louvain para todas las entidades que son nodos del grafo, este se encuentra en **/data/processed/louvain_malla_societaria_pesos/louvain_malla_societaria_pesos.csv** junto a un dataset con valores de modularidad vs resolucion en el calculo de la particion del grafo **/data/processed/louvain_malla_societaria_pesos/resolucion_modularidad_sociedad_pesos.csv**. Esta ultima data tambien es desplegada graficamente en la ejecucion de este script.
   
6. Ademas de ello, se presentan los siguientes notebooks que informan la performance del algoritmo en cada configuracion en relacion a los grupos economicos conocidos. Estos son:

    - **notebooks/performance_agrupacion_old/evaluacion_grupos_economicos_louvain_sociedades.ipynb**
    
    - **notebooks/performance_agrupacion_old/evaluacion_grupos_economicos_louvain_sociedad_contador.ipynb**
    
    - **notebooks/performance_agrupacion_old/evaluacion_grupos_economicos_louvain_sociedad_contador_representante.ipynb**
    
    - **notebooks/performance_agrupacion_old/evaluacion_grupos_economicos_louvain_sociedad_contador_representante_familiar.ipynb**
    
    - **notebooks/performance_agrupacion_old/evaluacion_grupos_economicos_louvain_sociedades_porcentaje_participacion.ipynb**

### Ejecuciones con optimización y pesos de relaciones. 

En esta parte, se aplican técnicas de optimización y se asignan pesos a las relaciones dentro del grafo, lo que permite un análisis más detallado y preciso de las comunidades dentro de los grupos económicos.

1. **Generacion de relaciones**
   - A partir de la data disponible, se construyen las relaciones totales y las entidades involucradas y su naturaleza para su posterio utilizacion en la creacion del grafo y el dataset que tendra la clasificacion final de cada entidad. Esto es regulado por el archivo **scr/data/Capas_relaciones_nodos.ipynb**, y que al ejecutarse guarda los siguientes archivos como datos procesados.
   - **/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_malla_societaria.csv**
   - **data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_familiares.csv**
   - **data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_contador.csv**
   - **data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_representante.csv**
   - **data/processed/nodos_relaciones_pregrupos_for_louvain/nodos.csv**
   - **data/processed/nodos_relaciones_pregrupos_for_louvain/grupos_previos.json**. Este archivo servia como insumo de comunidades iniciales para el algoritmo de Louvain, lo cual no mostro mejoras significativas en el producto final.
     
3. **Submuestra del Grafo**
   - Primero se probó con una muestra aleatoria del grafo que consideraba un porcentaje inicial del 10% del grafo conservando la representatividad del grafo inicia, pero no fue satisfactoria.
   - Luego se utilizó una muestra basada en la centralidad, seleccionando el 10% de los nodos con mayor centralidad. Esta muestra resultó más prometedora y se obtiene mediante el ejecutable **scr/models/definitivo/calculo_subgrafo/calculo_subgrafo_centralidad_gridsearch.py**, el cual tiene los siguientes outputs:
   - **data/processed/subgrafo/muestreo_centralidad_gridsearch/subgraph_filtrado.graphml**, subgrafo.
   - **data/processed/subgrafo/muestreo_centralidad_gridsearch/membership.json**, pertenencia de cada nodo a un grupo especifico inicial  en el subgrafo.
   - **data/processed/subgrafo/muestreo_centralidad_gridsearch/diccionario_grupos_muestra.json**. Diccionario de los nodos del subgrafo que pertenecen a los grupos definidos por criterio experto. 
   -   A partir de ello se decidio modular los pesos de las relaciones mediante una busqueda. Inicialmente se utilizo un criterio en el cual cada peso de relacion variaba de forma independiente para aislar el efecto de cada relacion especifica, pero por el tiempo de computo excesito se busco un metodo mas efectivo. Por ello finalmente se utilizo el mecanismo de evolucion diferencial aplicado en Python para que en una serie de iteraciones y bajo ciertos criterios de convergencia, se encontrara el mejor indice AMI. Esto se obtiene al ejecutar el archivo **scr/models/definitivo/louvain_gridsearch_submuestra_centralidad_with_optimizer.py**, que tiene como salida un archivo con la performance para cada combinacion de parametros en **data/processed/resultados_subgrafo_gridsearch/gridsearch_optimizator.csv**
   - Se hizo una comparación con los grupos económicos de este subgrafo, obteniendo valores de Adjusted Mutual Information (AMI) consistentes con los resultados obtenidos de AMI para grafos sin peso en sus relaciones y que estan incluidos en el archivo anterior.

4. **Optimización del Grafo**
   - Se asignan pesos a las relaciones según su importancia o valor, mejorando la precisión de las particiones, tomando en consideracion el mejor resultado del Gridsearch.
   - Se aplican algoritmos de Louvain con esos pesos especificos para las relaciones de tipo familiar, contador y representante. Todo este proceso se lleva a cabo por el ejecutable **scr/models/definitivo/louvain_complete.py**.

5. **Generación de Resultados**
   - Al igual que en la primera parte, cada configuración genera un archivo de salida con una clasificación de Louvain, pero en este caso, considerando los pesos y las optimizaciones aplicadas para todo el grafo, dando como resultado el archivo final con la clasificacion para cada entidad **data/processed/resultados_finales/louvain/louvain_all.csv** **data/processed/resultados_finales/louvain/resolucion_modularidad_louvain_all.csv**. Ademas,los datos de la clasificación son guardaddos en formato parque en **abfs://data@datalakesii.dfs.core.windows.net/DatosOrigen/lr-629/agrupacion_empresas_similares/louvain_final**. Nuevamente se toman esos resultados, filtrando la comunidad para las entidades con grupo definido y verificando que el AMI sea coherente con el observado en el GridSearch, lo cual se analiza brevemente en el archivo **notebooks/performance_agrupacion_new/Performance final execution.ipynb**.
  
Esta serie de pasos explica la ejecucion y decisiones tomadas durante el proyecto y su ejecucion. 


## Explicacion adicional
***
Como se menciono previamente, varias tecnicas fueron desechadas durante el intento de particion del grafo, mas especificamente la implementacion del algoritmo de Leiden por su baja performance en el AMI  de las muestras. Por otro lado, se deshecha la construccion de la muestra del 10% del grafo como muestra aleatoria representativa, lo cual ya fue mencionado en la seccion anterior.

## Sugerencias
***
Una sugerencia posible es lograr ver si las comunidades iniciales son utiles para inicializar el grafico con esos nodos en dichos grupos, mas alla que la ejecucion de Louvain se detenga con un error del tipo *Bad graph type*.

## Plantilla del proyecto
***
Se especifica a continuacion la estructura del proyecto.

Proyecto/
│			
├── notebooks/          				# Jupyter notebooks para exploración de datos, prototipado de modelos, etc.

│   ├── [noteebok1.ipynb]			

│   ├── [notebook2.ipynb]		

│   ├── [notebook3.ipynb]		

│			
├── src/                				# Código fuente Python

│   ├── data/           				# Módulos para cargar, limpiar y procesar datos.

│   ├── models/         				# Definiciones de modelos

│   ├── evaluation/     				# Scripts para evaluar el rendimiento de los modelos.

│   └── utils/          				# Utilidades y funciones auxiliares.

│			

├── data/        				        # Bases de dato de todo tipo que se utilizan o generan en el proyecto.

│   ├── external/     				    # Data externa

│   ├── processed/          			# Data procesada

│   └── raw/                            # Data cruda

│					

├── requirements.txt    				# Archivo de requisitos para reproducir el entorno de Python.

│			

└── readme.md           				# Descripción general del proyecto y su estructura.

** Archivos entre [ ] son ejemplos solamente y no se entregan por ahora.

