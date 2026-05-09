# AGENT — WordPress REST API Integration

## Role
Push content (posts, pages, metadata) to any WordPress site via the WP REST API.
Reads from the IAC pipeline (Agent #6 SEO tasks, Agent #9 implementation log,
Agent #10 deployment manifest) and publishes directly to the target WP instance.

---

## Configuration (set before execution)

```
WP_API_URL      = "https://bkt-agency.com/wp-json/wp/v2"
WP_USERNAME     = "YOUR_WP_USERNAME"
WP_APP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"   # WordPress Application Password
                                                      # Generate: WP Admin → Users → Profile → Application Passwords
```

**Security rules:**
- NEVER commit `WP_APP_PASSWORD` to version control.
- Store in environment variable or secrets manager (e.g., `.env`, AWS Secrets Manager, Doppler).
- Use Application Passwords only — do not use account password directly.
- All requests must use HTTPS. HTTP blocked.

---

## Endpoints

### Posts — `/wp-json/wp/v2/posts`

```
GET    /wp-json/wp/v2/posts              → List all posts
GET    /wp-json/wp/v2/posts/{id}         → Get single post
POST   /wp-json/wp/v2/posts              → Create new post
PUT    /wp-json/wp/v2/posts/{id}         → Full update
PATCH  /wp-json/wp/v2/posts/{id}         → Partial update
DELETE /wp-json/wp/v2/posts/{id}         → Trash post
DELETE /wp-json/wp/v2/posts/{id}?force=true → Permanent delete
```

**Create Post — request body schema:**
```json
{
  "title":   "Post Title",
  "content": "<!-- wp:paragraph --><p>Body content.</p><!-- /wp:paragraph -->",
  "slug":    "post-slug",
  "status":  "publish",
  "categories": [1],
  "tags":       [5, 12],
  "meta": {
    "_yoast_wpseo_title":    "SEO Title | BKT Agency",
    "_yoast_wpseo_metadesc": "Meta description max 155 chars.",
    "_yoast_wpseo_focuskw":  "target keyword"
  }
}
```

---

### Pages — `/wp-json/wp/v2/pages`

```
GET    /wp-json/wp/v2/pages              → List all pages
GET    /wp-json/wp/v2/pages/{id}         → Get single page
POST   /wp-json/wp/v2/pages              → Create new page
PUT    /wp-json/wp/v2/pages/{id}         → Full update
PATCH  /wp-json/wp/v2/pages/{id}         → Partial update
DELETE /wp-json/wp/v2/pages/{id}         → Trash page
```

**Create Page — request body schema:**
```json
{
  "title":    "Page Title",
  "content":  "<!-- wp:paragraph --><p>Page body.</p><!-- /wp:paragraph -->",
  "slug":     "page-slug",
  "status":   "publish",
  "template": "",
  "parent":   0,
  "meta": {
    "_yoast_wpseo_title":    "Page SEO Title | BKT Agency",
    "_yoast_wpseo_metadesc": "Page meta description.",
    "_yoast_wpseo_focuskw":  "primary keyword"
  }
}
```

---

### Media — `/wp-json/wp/v2/media`

```
POST /wp-json/wp/v2/media
Headers: Content-Type: image/jpeg
         Content-Disposition: attachment; filename="image.jpg"
Body:    [raw image binary]
```

---

## Authentication

All write operations require HTTP Basic Auth with Application Password:

```python
import requests, base64, os

WP_API_URL      = os.getenv("WP_API_URL")       # e.g. https://bkt-agency.com/wp-json/wp/v2
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

credentials = base64.b64encode(
    f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()
).decode("utf-8")

HEADERS = {
    "Authorization": f"Basic {credentials}",
    "Content-Type":  "application/json"
}
```

---

## IAC Integration — Agent Pipeline Push Functions

```python
def push_seo_page(slug: str, title: str, content: str, focus_kw: str, meta_desc: str) -> dict:
    """Agent #9/#10 → WP: Create or update a page from deployment manifest."""
    payload = {
        "title":   title,
        "content": content,
        "slug":    slug,
        "status":  "publish",
        "meta": {
            "_yoast_wpseo_title":    f"{title} | BKT Agency",
            "_yoast_wpseo_metadesc": meta_desc,
            "_yoast_wpseo_focuskw":  focus_kw
        }
    }
    r = requests.post(f"{WP_API_URL}/pages", json=payload, headers=HEADERS)
    r.raise_for_status()
    return r.json()


def push_blog_post(title: str, content: str, focus_kw: str, meta_desc: str,
                   categories: list = None, tags: list = None) -> dict:
    """Agent #6 → WP: Publish SEO blog post from seo_recommendations.json task."""
    payload = {
        "title":      title,
        "content":    content,
        "slug":       title.lower().replace(" ", "-"),
        "status":     "publish",
        "categories": categories or [],
        "tags":       tags or [],
        "meta": {
            "_yoast_wpseo_title":    f"{title} | BKT Agency",
            "_yoast_wpseo_metadesc": meta_desc,
            "_yoast_wpseo_focuskw":  focus_kw
        }
    }
    r = requests.post(f"{WP_API_URL}/posts", json=payload, headers=HEADERS)
    r.raise_for_status()
    return r.json()


def inject_schema_to_page(page_id: int, schema_json: dict) -> dict:
    """Agent #10 → WP: Inject JSON-LD schema block into existing page head via meta."""
    payload = {
        "meta": {
            "_custom_schema_json_ld": str(schema_json)
        }
    }
    r = requests.patch(f"{WP_API_URL}/pages/{page_id}", json=payload, headers=HEADERS)
    r.raise_for_status()
    return r.json()
```

---

## Error Handling

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 401 | Bad credentials | Regenerate Application Password in WP Admin |
| 403 | Insufficient permissions | Ensure WP user role is Editor or Administrator |
| 404 | Post/page not found | Verify ID; run GET to list available IDs |
| 422 | Validation error | Check required fields; verify slug uniqueness |
| 500 | WP server error | Check WP debug.log; verify REST API not disabled |

---

## IAC Contract

| Direction    | File |
|--------------|------|
| Reads from   | `site_deployment_manifest.json` (Agent #10) |
| Reads from   | `seo_recommendations.json` (Agent #6) |
| Reads from   | `seo_implementation_log.json` (Agent #9) |
| Reads config | `BRAND_IDENTITY.json` |
| Target site  | `WP_API_URL` (env var) |
