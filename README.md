# 📚 API - Sistema de Doação de Livros

**Base URL**: `http://127.0.0.1:5000`  
**Autenticação**: **Bearer Token (JWT)**

Adicione este header em rotas protegidas:

```
Authorization: Bearer <seu_token_jwt>
Content-Type: application/json
```

---

## 🔐 Auth

### `POST /auth/register`

📌 **Registrar novo usuário**

```json
{
  "email": "example@example.com",
  "nickname": "example",
  "password": "example123"
}
```

---

### `POST /auth/login`

📌 **Login do usuário**

```json
{
  "email": "example@example.com",
  "password": "example123"
}
```

**Resposta:**

```json
{
  "access_token": "<token_jwt>"
}
```

---

### `POST /auth/logout`

📌 **Logout do usuário (invalida o token)**  
**Headers:**

```
Authorization: Bearer <token>
```

---

### `POST /auth/forgot-password`

📌 **Enviar e-mail para recuperação de senha**

```json
{
  "email": "example@example.com"
}
```

---

### `POST /auth/reset-password/<token>`

📌 **Redefinir senha com token**
**Headers:**

```
Authorization: Bearer <token>
```

```json
{
  "new_password": "NovaSenha@2025",
  "confirm_password": "NovaSenha@2025"
}
```

---

## 👤 Users

### `GET /users/<id>`

📌 **Detalhes de um usuário**  
Exemplo: `/users/f17768a7-080c-4422-925f-f554344f54e5`

---

### `PUT /users/<id>`

📌 **Atualizar dados do perfil**  
**Headers:**  
`Authorization: Bearer <token>`

```json
{
  "nickname": "novo_nickname",
  "email": "novoemail@example.com"
}
```

---

### `GET /users/<id>/books`

📌 **Listar livros cadastrados por um usuário**  
Exemplo: `/users/6ccb4d7d-aa6a-4608-880f-92d5be706891/books`

---

### `PUT /users/password`

📌 **Atualizar senha do usuário**  
**Headers:**  
`Authorization: Bearer <token>`

```json
{
  "old_password": "senhaAntiga123",
  "new_password": "NovaSenha@2025"
}
```

---

## 📚 Books

### `GET /books`

📌 **Listar todos os livros disponíveis**  
**Headers:**  
`Authorization: Bearer <token>`

---

### `GET /books/<termo>`

📌 **Buscar livros por título ou autor**  
Exemplo: `/books/teste`

---

### `POST /books`

📌 **Cadastrar novo livro**  
**Headers:**  
`Authorization: Bearer <token>`

```json
{
  "title": "Dom Casmurro",
  "author": "Machado de Assis",
  "category": "Literatura",
  "image_url": "https://teste.com/imagem.jpg"
}
```

---

### `PUT /books/<id>`

📌 **Editar informações de um livro**  
**Headers:**  
`Authorization: Bearer <token>`

```json
{
  "title": "Novo Título",
  "author": "Novo Autor",
  "category": "Nova Categoria",
  "image_url": "https://example.com/image.jpeg"
}
```

---

### `DELETE /books/<id>`

📌 **Remover um livro**  
**Headers:**  
`Authorization: Bearer <token>`
