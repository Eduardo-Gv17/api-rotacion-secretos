import os
import boto3
import pymysql
import random
import string


ssm = boto3.client("ssm")


def generar_password():

    caracteres = string.ascii_letters + string.digits + "@#$%"

    return ''.join(random.choice(caracteres) for _ in range(16))


def actualizar_usuario(cursor, usuario, nuevo_password):

    sql = f"ALTER USER '{usuario}'@'%' IDENTIFIED BY '{nuevo_password}'"

    cursor.execute(sql)


def actualizar_parameter_store(nombre, password):

    ssm.put_parameter(

        Name=nombre,

        Value=password,

        Type="SecureString",

        Overwrite=True

    )


def lambda_handler(event, context):

    host = ssm.get_parameter(

        Name=os.environ["DB_HOST_PARAMETER"],

        WithDecryption=True

    )["Parameter"]["Value"]

    connection = pymysql.connect(

        host=host,

        user=os.environ["DB_ADMIN_USER"],

        password=os.environ["DB_ADMIN_PASSWORD"],

        connect_timeout=5

    )

    usuarios = {

        "user_dev": "/rds_mysql_alumnos/user_dev/password",

        "user_test": "/rds_mysql_alumnos/user_test/password",

        "user_prod": "/rds_mysql_alumnos/user_prod/password"

    }

    try:

        with connection.cursor() as cursor:

            for usuario, parametro in usuarios.items():

                nuevo = generar_password()

                actualizar_usuario(

                    cursor,

                    usuario,

                    nuevo

                )

                actualizar_parameter_store(

                    parametro,

                    nuevo

                )

                print(

                    f"{usuario} actualizado."

                )

        connection.commit()

        return {

            "statusCode": 200,

            "body": "Rotación completada."

        }

    except Exception as e:

        connection.rollback()

        return {

            "statusCode": 500,

            "body": str(e)

        }

    finally:

        connection.close()