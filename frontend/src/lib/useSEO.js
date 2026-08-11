import { useEffect } from "react";

/**
 * Lightweight SEO hook that manages the document title and per-page meta tags
 * without external dependencies. It sets/updates:
 *  - <title>
 *  - meta[name="description"]
 *  - meta[name="keywords"] (optional)
 *  - Open Graph tags (og:title, og:description, og:image, og:url, og:type)
 *  - Twitter Card tags
 *  - <link rel="canonical">
 *  - Optional JSON-LD structured data (script[type="application/ld+json"] id="lp-jsonld")
 *
 * On unmount it leaves the tags in place so the next page can overwrite them;
 * every call re-writes the same DOM nodes, keeping the head clean.
 */

function upsertMeta(selector, attrs) {
  let el = document.head.querySelector(selector);
  if (!el) {
    el = document.createElement("meta");
    Object.entries(attrs.create || {}).forEach(([k, v]) => el.setAttribute(k, v));
    document.head.appendChild(el);
  }
  Object.entries(attrs.set || {}).forEach(([k, v]) => {
    if (v == null) return;
    el.setAttribute(k, v);
  });
}

function setLink(rel, href) {
  if (!href) return;
  let el = document.head.querySelector(`link[rel="${rel}"]`);
  if (!el) {
    el = document.createElement("link");
    el.setAttribute("rel", rel);
    document.head.appendChild(el);
  }
  el.setAttribute("href", href);
}

function setJsonLd(id, data) {
  const existing = document.getElementById(id);
  if (!data) {
    if (existing) existing.remove();
    return;
  }
  const script = existing || document.createElement("script");
  script.type = "application/ld+json";
  script.id = id;
  script.text = JSON.stringify(data);
  if (!existing) document.head.appendChild(script);
}

export function useSEO({
  title,
  description,
  keywords,
  image,
  url,
  type = "website",
  locale = "it_IT",
  jsonLd,
  jsonLdId = "lp-jsonld",
} = {}) {
  useEffect(() => {
    const siteName = "LicenzPøl";
    const fullTitle = title
      ? (title.toLowerCase().includes("licenzp") ? title : `${title} — ${siteName}`)
      : `${siteName} — Il software giusto, senza fatica`;
    document.title = fullTitle;

    // Canonical
    const canonical = url || (typeof window !== "undefined" ? window.location.href : undefined);
    setLink("canonical", canonical);

    // Description
    if (description) {
      upsertMeta('meta[name="description"]', {
        create: { name: "description" },
        set: { content: description },
      });
    }
    if (keywords) {
      upsertMeta('meta[name="keywords"]', {
        create: { name: "keywords" },
        set: { content: keywords },
      });
    }

    // Open Graph
    upsertMeta('meta[property="og:title"]', {
      create: { property: "og:title" },
      set: { content: fullTitle },
    });
    upsertMeta('meta[property="og:type"]', {
      create: { property: "og:type" },
      set: { content: type },
    });
    upsertMeta('meta[property="og:site_name"]', {
      create: { property: "og:site_name" },
      set: { content: siteName },
    });
    upsertMeta('meta[property="og:locale"]', {
      create: { property: "og:locale" },
      set: { content: locale },
    });
    if (description) {
      upsertMeta('meta[property="og:description"]', {
        create: { property: "og:description" },
        set: { content: description },
      });
    }
    if (canonical) {
      upsertMeta('meta[property="og:url"]', {
        create: { property: "og:url" },
        set: { content: canonical },
      });
    }
    if (image) {
      const absImage = image.startsWith("http")
        ? image
        : (typeof window !== "undefined" ? `${window.location.origin}${image}` : image);
      upsertMeta('meta[property="og:image"]', {
        create: { property: "og:image" },
        set: { content: absImage },
      });
      upsertMeta('meta[name="twitter:image"]', {
        create: { name: "twitter:image" },
        set: { content: absImage },
      });
    }

    // Twitter
    upsertMeta('meta[name="twitter:card"]', {
      create: { name: "twitter:card" },
      set: { content: image ? "summary_large_image" : "summary" },
    });
    upsertMeta('meta[name="twitter:title"]', {
      create: { name: "twitter:title" },
      set: { content: fullTitle },
    });
    if (description) {
      upsertMeta('meta[name="twitter:description"]', {
        create: { name: "twitter:description" },
        set: { content: description },
      });
    }

    // JSON-LD
    setJsonLd(jsonLdId, jsonLd);

    return () => {
      // Only remove the per-page JSON-LD on unmount — meta tags are overwritten by the next page.
      const s = document.getElementById(jsonLdId);
      if (s) s.remove();
    };
  }, [title, description, keywords, image, url, type, locale, JSON.stringify(jsonLd), jsonLdId]);
}

export default useSEO;
