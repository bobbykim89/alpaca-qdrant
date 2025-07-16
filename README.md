# ALPACA-Qdrant: Vercel Serverless Function – `/api/search`

This is a Vercel serverless function that provides a simple API endpoint for hybrid semantic search using [Qdrant](https://qdrant.tech/).

## 📌 Route

```sh
/api/search
```

## 📤 Methods

### `GET /api/search`

Returns a brief JSON object describing the purpose of this endpoint.

**Response Example:**

```json
{
  "message": "This route only support POST method.",
  "data": {
    "selected_career": "selected career from quiz",
    "answers": ["answers from quiz"]
  }
}
```

---

### `POST /api/search`

Performs a hybrid search using Qdrant based on the given input.

**Request Body:**

```json
{
  "answers": ["<answers from questionnaire>..."],
  "selected_career": "<selected career name>"
}
```

- `query` _(string)_ – The search term.
- `filters` _(optional object)_ – Additional metadata to filter results (e.g., by degree level).

**Response:**
Returns the top 5 most relevant degree program results as determined by the hybrid search.

**Response Example:**

```json
{
  "message": "Submission received",
  "request": {
    "selected_career": "<selected career name>",
    "user_profile": "<answers from request body formatted in string>..."
  },
  "data": ["<qdrant search results>..."]
}
```

---

## 🧠 Powered By

- [Qdrant Client](https://qdrant.tech/documentation/)
- Vercel Serverless Functions

## 🚀 Deployment

This function is deployed via [Vercel](https://vercel.com/docs/functions/serverless-functions/introduction). To test locally or deploy updates:

```bash
vercel dev
```

Or deploy to production:

```bash
vercel --prod
```
