# Decisiones de arquitectura

> Este documento lista y explica la diferentes decisiones de arquitectura que se han ido
> realizando durante el desarrollo de la solución.

---

Generalmente se optará por recursos serverless, ya que se espera que el MVP sea utilizado principalmente por 2 personas, por lo que para minimizar el coste a la vez que se asegura la escalabilidad en caso de decidir abrirlo a más usuarios, será importante el pago por uso y la capacidad de escalar cualquier recurso a 0 cuando no se use. Por la naturaleza de la aplicación, el tráfico esperado será por el día y esporádico, para consultar y actualizar el menú semanal o la lista de la compra.

- Para el frontend, se ha optado por una single page app, aumentando así la dependencia del backend para mostrar la aplicación pero simplificando considerablemente el desarrollo frontend, en el cual tengo mucha menos experiencia. En AWS se intentará utilizar de primeras, al ser una página estática, un recurso CloudFront con el sitio alojado en un bucket S3, al ser una solución sencilla y escalable que asegura siempre un servidor cercano a cualquier usuario en las edge locations.

- Para la base de datos, como opción serverless, se utilizará DynamoDB, que ofrece rapidez y escalabilidad con el modelo de pago por uso. Se adaptará el modelo de datos para este tipo de base de datos.

- Para gestión de usuarios, se hará en el backend con la base de datos DynamoDB como respaldo.

- En cuanto al backend, siguiendo con la filosofía serverless del proyecto, se utilizarán funciones Lambda. Esto facilita el escalado y permite enfocar el funcionamiento de la app para que sea orientado a eventos. Se utilizarán dos funciones Lambda: una que expondrá los endpoints necesarios para que el frontend realice operaciones, y otra que se ocupará de las operaciones de IA en forma de workers, activadas por una cola.

- Para hacer las operaciones de generación con IA asíncronas, se utilizará una cola SQS estándar con control de idempotencia implementado en los workers. No se usa una cola FIFO porque requiere que se respete el orden y por tanto no permite que los workers trabajen de forma paralela. De esta forma se asegurará que las solicitudes sean ejecutadas por 1 worker y no haya generaciones duplicadas.

- Para exponer las APIs del backend a las que el frontend tiene que llamar de forma segura se usará API Gateway. De esta forma no se exponen las Lambdas a la red pública y se mejora la seguridad de la aplicación.