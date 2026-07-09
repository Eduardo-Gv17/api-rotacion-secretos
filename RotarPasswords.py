import boto3
import pymysql
import random
import string
import os

# ---------- CONFIGURACIÓN ----------

ADMIN_USER = "admin"
ADMIN_PASSWORD = "MiClaveSegura123"

HOST_PARAMETER = os.environ["DB_HOST_PARAMETER"]

ssm = boto3.client("ssm")

# Usuarios a rotar
USUARIOS = {
    "user_dev": "/rds_mysql_alumnos/user_dev/password",
    "user_test": "/rds_mysql_alumnos/user_test/password",
    "user_prod": "/rds_mysql_alumnos/user_prod/password"
}


# ---------- FUNCIONES ----------

def obtener_host():

    response = ssm.get_parameter(
        Name=HOST_PARAMETER,
        WithDecryption=True
    )

    return response["Parameter"]["Value"]


def generar_password():

    caracteres = (
        string.ascii_letters +
        string.digits +
        "@#$%&*!"
    )

    return "".join(random.choice(caracteres) for _ in range(16))


def actualizar_parameter(nombre, password):

    ssm.put_parameter(
        Name=nombre,
        Value=password,
        Type="SecureString",
        Overwrite=True
    )


# ---------- LAMBDA ----------

def lambda_handler(event, context):

    host = obtener_host()

    conexion = pymysql.connect(
        host=host,
        user=ADMIN_USER,
        password=ADMIN_PASSWORD,
        connect_timeout=5
    )

    try:

        with conexion.cursor() as cursor:

            for usuario, parametro in USUARIOS.items():

                nueva_password = generar_password()

                sql = (
                    f"ALTER USER '{usuario}'@'%' "
                    f"IDENTIFIED BY '{nueva_password}'"
                )

                cursor.execute(sql)

                actualizar_parameter(
                    parametro,
                    nueva_password
                )

                print(
                    f"{usuario} actualizado correctamente."
                )

        conexion.commit()

        return {
            "statusCode": 200,
            "body": "Rotación completada."
        }

    except Exception as e:

        conexion.rollback()

        return {
            "statusCode": 500,
            "body": str(e)
        }

    finally:
