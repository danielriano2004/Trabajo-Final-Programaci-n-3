Directrices Estructurales y Parámetros para los Archivos de Conocimiento
Para garantizar la estabilidad matemática del pipeline de extracción y evitar degradaciones en la precisión del motor de búsqueda semántica, todos los documentos que se ingresen a la carpeta de ingesta masiva local o que se carguen de manera dinámica a través de la interfaz del bot deben cumplir rigurosamente con las siguientes especificaciones técnicas de formato y arquitectura de datos. El incumplimiento de estas pautas no provocará un colapso en el código del servidor, pero anulará las ventajas del filtro híbrido y distorsionará la calidad de las respuestas generadas por el modelo de lenguaje.

En primer lugar, el sistema restringe su compatibilidad exclusivamente a archivos de texto plano estructurados bajo la codificación de caracteres universales UTF-8 con extensión .txt, y a documentos de almacenamiento digital PDF con extensión .pdf. Cualquier otro formato como documentos procesados de texto o extensiones enriquecidas de código serán rechazados automáticamente por la pasarela de red y los módulos locales de control para proteger la integridad del almacenamiento físico del servidor.

En segundo lugar, se establece la Regla de Oro de la Primera Línea. El primer renglón absoluto de cada archivo de texto plano debe estar reservado de forma única para el título o tema central del documento redactado completamente en letras mayúsculas, sin la inclusión de caracteres especiales, saludos, fechas de edición o preámbulos introductorios. El script de automatización utiliza esta primera secuencia de caracteres como el ancla de metadatos principal para indexar el vector en la base de datos espacial. Si un documento posee un párrafo extenso o un texto aleatorio en su primera línea, el sistema asumirá que dicha frase es el nombre del tema, corrompiendo la posterior fase de comparación lingüística. Como mecanismo de contingencia y salvavidas ante el desorden de los datos provistos por el usuario, si el software detecta que la primera línea es inválida o supera los sesenta caracteres, procederá a limpiar el nombre físico del archivo en disco (eliminando guiones y la extensión) para utilizarlo como título de respaldo estructural.

En tercer lugar, el cuerpo del conocimiento técnico debe desarrollarse formalmente a partir de la segunda línea del archivo utilizando una densidad de información controlada. Se debe evitar la fragmentación excesiva del texto en líneas huérfanas o palabras sueltas separadas por renglones vacíos. El algoritmo de segmentación divide la información en bloques fijos de ciento veinte palabras; si un párrafo mezcla múltiples conceptos radicalmente opuestos sin una transición temática fluida, dichos conceptos quedarán fusionados dentro de la misma matriz numérica, diluyendo la pureza semántica del embedding y provocando que el modelo de lenguaje reciba un contexto cruzado que afectará su capacidad de deducción lógica.

1. Arquitectura del Sistema
El sistema está diseñado bajo un enfoque de microservicios e infraestructura como código, dividiendo el software en dos grandes capas operacionales que interactúan de manera desacoplada a través de protocolos de red interna. La capa de infraestructura se encuentra completamente contenerizada y es gestionada por un motor de virtualización a nivel de sistema operativo. Esta capa aísla los entornos de ejecución a nivel de núcleo de los servicios centrales, los cuales consisten en un motor de persistencia vectorial desarrollado en Rust y un servidor de inferencia de inteligencia artificial programado en C++. Este diseño garantiza la portabilidad absoluta del ecosistema, permitiendo un despliegue inmediato en cualquier plataforma anfitriona y eliminando los conflictos habituales de dependencias lógicas y configuraciones de hardware locales.

Por otro lado, la capa de control y lógica de negocio se ejecuta de manera local mediante scripts optimizados que gestionan el flujo completo de los datos. Esta capa es la encargada de coordinar el pipeline de extracción, realizar la limpieza y unificación de textos procedentes de archivos corruptos o mal alineados, y orquestar el algoritmo híbrido de búsqueda. Asimismo, implementa un bucle continuo de escucha activa que funciona como pasarela de comunicación con los servidores externos de la plataforma de mensajería, permitiendo recibir solicitudes, auditar el estado del repositorio vectorial y despachar las respuestas estructuradas en tiempo real.

2. Tecnologías y Librerías Utilizadas
El entorno de infraestructura utiliza imágenes contenerizadas optimizadas para el rendimiento matemático y de red. El motor de persistencia vectorial almacena de forma eficiente las matrices numéricas de los bloques de texto y realiza los cálculos de similitud geométrica en un plano multidimensional. El entorno de ejecución de redes neuronales local se encuentra optimizado para permitir el consumo eficiente de recursos físicos de memoria volátil y procesamiento, permitiendo la ejecución de modelos de lenguaje avanzados sin depender de servicios externos en la nube.

El código fuente de control se apoya en una serie de paquetes de terceros especializados para garantizar la robustez del pipeline. Se emplean herramientas de análisis binario para decodificar cadenas de texto en bruto desde archivos PDF, removiendo automáticamente anomalías visuales y espaciados huérfanos. Los kits de desarrollo oficial facilitan la comunicación interna con los puertos locales del servidor de inferencia y de la base de datos vectorial mediante interfaces estandarizadas de consulta. El aseguramiento de credenciales y tokens de acceso se realiza a través de componentes de inyección de variables de entorno, mientras que la pila de red gestiona conexiones HTTP persistentes con los endpoints remotos de la API de comunicación. Finalmente, se aplican módulos naticos del lenguaje para el escaneo del sistema de archivos, la limpieza de secuencias de texto mediante expresiones regulares, la serialización de estructuras de datos y el monitoreo de latencias en milisegundos.

📊 3. Especificaciones del Motor RAG e Inferencia
El proyecto implementa un pipeline de generación aumentada por recuperación parametrizado bajo un estricto control matemático para asegurar respuestas de alta fidelidad. El proceso de representación vectorial transforma los bloques de texto en matrices fijas de setecientas sesenta y ocho dimensiones conceptuales abstractas. Cuando un usuario realiza una consulta, el sistema convierte la pregunta en un vector y extrae los cinco fragmentos con mayor similitud geométrica calculada mediante la métrica de distancia coseno.

Para optimizar la recuperación ante términos propios del videojuego, el motor ejecuta un algoritmo de re-rankeo híbrido que combina la búsqueda espacial con el análisis léxico directo. Si las palabras clave de la consulta coinciden exactamente con el título interno del documento indexado o con su nombre de respaldo, el fragmento recibe una bonificación fija de puntuación de más cero punto quince, priorizando los datos específicos sobre la similitud conceptual abstracta. Posteriormente, se aplica un filtro de seguridad con un umbral crítico de cero punto treinta y cinco; cualquier entidad matemática que posea una confianza inferior a este límite es descartada inmediatamente para evitar la introducción de ruido o datos ajenos al contexto. Los fragmentos aprobados se inyectan en un entorno de inferencia condicionado junto con las instrucciones del sistema, obligando al modelo autorregresivo de dos mil millones de parámetros a redactar un texto fluido y natural basado exclusivamente en la información verídica recuperada de los archivos técnicos.

4. Manual de Despliegue e Instalación
Para replicar el entorno inmutable de desarrollo y producción local en cualquier sistema anfitrión, ejecute los comandos en la terminal respetando estrictamente el orden secuencial establecido.

Paso 1: Clonar y Preparar el Entorno de Python
Sitúese en el directorio raíz del proyecto e instale el conjunto general de bibliotecas de control requeridas por los scripts del sistema:

Bash
pip install pypdf ollama qdrant-client python-dotenv requests standard-tokenizer
Paso 2: Despliegue de los Contenedores de Infraestructura Aislada
Asegúrese de que el motor de virtualización esté activo y ejecute la inicialización de los servicios de soporte en segundo plano:

Bash
docker compose up -d
Paso 3: Aprovisionamiento Local de los Modelos de Inteligencia Artificial
Inyecte las instrucciones de descarga de los pesos neuronales directamente en la consola interactiva del contenedor virtualizado de inferencia:

Bash
docker exec -it ollama_container ollama run nomic-embed-text
docker exec -it ollama_container ollama run gemma2:2b
Paso 4: Carga e Indexación de Conocimiento (Pipeline ETL)
Deposite los documentos base de la enciclopedia dentro del directorio local y ejecute el script de poblamiento inicial para limpiar la base de datos, segmentar los textos y subir las matrices numéricas a Qdrant:

Bash
python intake.py
Paso 5: Inicialización del Bot de Telegram (Producción Local)
Inicie el script principal para activar el bucle continuo de escucha de red, habilitar la telemetría del servidor y conectar el servicio interactivo de asistencia en tiempo real:

Bash
python bot.py



cualquier falta al procedimiento del manejo de los archivos y la creacion de los mismos puede dar lugar a un mal funcionamiento de la aplicacion.