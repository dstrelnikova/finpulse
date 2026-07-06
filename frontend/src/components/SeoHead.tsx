import { useEffect } from "react";

type SeoHeadProps = {
  title: string;
  description: string;
  canonicalPath: string;
  image?: string;
  type?: "website" | "article";
  noindex?: boolean;
  structuredData?: Record<string, unknown>;
};

const SITE_URL = import.meta.env.VITE_SITE_URL ?? "http://localhost:3000";
const DEFAULT_IMAGE = `${SITE_URL}/icon.png`;

function upsertNamedMeta(name: string, value: string) {
  let node = document.head.querySelector(`meta[name="${name}"]`) as HTMLMetaElement | null;
  if (!node) {
    node = document.createElement("meta");
    node.setAttribute("name", name);
    document.head.appendChild(node);
  }
  node.setAttribute("content", value);
}

function upsertPropertyMeta(property: string, value: string) {
  let node = document.head.querySelector(`meta[property="${property}"]`) as HTMLMetaElement | null;
  if (!node) {
    node = document.createElement("meta");
    node.setAttribute("property", property);
    document.head.appendChild(node);
  }
  node.setAttribute("content", value);
}

export default function SeoHead({
  title,
  description,
  canonicalPath,
  image,
  type = "website",
  noindex = false,
  structuredData,
}: SeoHeadProps) {
  useEffect(() => {
    const canonicalUrl = `${SITE_URL}${canonicalPath}`;
    const imageUrl = image || DEFAULT_IMAGE;

    document.title = title;
    upsertNamedMeta("description", description);
    upsertNamedMeta("robots", noindex ? "noindex, nofollow" : "index, follow");

    upsertPropertyMeta("og:title", title);
    upsertPropertyMeta("og:description", description);
    upsertPropertyMeta("og:type", type);
    upsertPropertyMeta("og:url", canonicalUrl);
    upsertPropertyMeta("og:image", imageUrl);

    let canonical = document.head.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.setAttribute("rel", "canonical");
      document.head.appendChild(canonical);
    }
    canonical.setAttribute("href", canonicalUrl);

    const jsonLdId = "finpulse-jsonld";
    const old = document.getElementById(jsonLdId);
    if (old) {
      old.remove();
    }

    if (structuredData) {
      const script = document.createElement("script");
      script.id = jsonLdId;
      script.type = "application/ld+json";
      script.text = JSON.stringify(structuredData);
      document.head.appendChild(script);
    }
  }, [title, description, canonicalPath, image, type, noindex, structuredData]);

  return null;
}
