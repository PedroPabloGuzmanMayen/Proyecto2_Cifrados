# Proyecto2_Cifrados

- Paso 1: crea un *.env* en la raíz del proyecto y en la raíz de la carpeta *Backend/src*

```bash

touch .env

touch Backend/src/.env

```

- Paso 2: añade estas credenciales a tu *.env*

```bash

POSTGRES_HOST=host
POSTGRES_USER=usuario
POSTGRES_PASSWORD=password
POSTGRES_DB=nombredb
POSTGRES_PORT=puerto
JWT_SECRET=secreto

```

Ajusta las credenciales según te convenga

- Paso 3: levanta el docker compose desde la raíz del proyecto

```bash

docker compose up -d

```

- Paso 4: Ahora puedes probar estos endpoints desde tu navgegador o desde un programa que te permite probar APIs como postman

```bash

/registro

{
  "name": "Juan Pérez",
  "email": "juan.perez@minfin.gob.gt",
  "contrasenas": "MiContraseña_Segura123!"
}

/login

{
  "email": "juan.perez@minfin.gob.gt",
  "contrasenas": "MiContraseña_Segura123!"
}

/user/userid/key

(ajustar el id del usuario)


```

- Paso 5: puedes ejecutar los tests así:

```bash

cd Backend/src

python -m pytest -v

```


