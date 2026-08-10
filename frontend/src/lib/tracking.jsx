import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SettingsCtx = createContext(null);

function ensureVisitorId() {
  let id = localStorage.getItem("lp_visitor_id");
  if (!id) {
    id = "v_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem("lp_visitor_id", id);
  }
  let sid = sessionStorage.getItem("lp_session_id");
  if (!sid) {
    sid = "s_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    sessionStorage.setItem("lp_session_id", sid);
  }
  return { visitor_id: id, session_id: sid };
}

function detectDevice() {
  const w = window.innerWidth;
  const ua = navigator.userAgent.toLowerCase();
  if (/mobile|iphone|android/.test(ua) && w < 640) return "mobile";
  if (w < 1024) return "tablet";
  return "desktop";
}

export async function trackEvent(evt) {
  try {
    const ids = ensureVisitorId();
    await axios.post(`${API}/analytics/track`, {
      ...ids,
      device_type: detectDevice(),
      referrer: document.referrer || null,
      language: document.documentElement.lang || "it",
      path: window.location.pathname,
      ...evt,
    });
  } catch { /* swallow */ }
}

function injectHead(id, html) {
  if (!html) return () => {};
  const existing = document.getElementById(id);
  if (existing) existing.remove();
  const wrap = document.createElement("div");
  wrap.id = id;
  wrap.innerHTML = html;
  // Move scripts to executable form
  const nodes = Array.from(wrap.childNodes);
  nodes.forEach(n => {
    if (n.tagName === "SCRIPT") {
      const s = document.createElement("script");
      Array.from(n.attributes || []).forEach(a => s.setAttribute(a.name, a.value));
      s.text = n.text;
      document.head.appendChild(s);
    } else {
      document.head.appendChild(n);
    }
  });
  return () => {
    const el = document.getElementById(id);
    if (el) el.remove();
  };
}

export function SiteSettingsProvider({ children }) {
  const [settings, setSettings] = useState(null);

  useEffect(() => {
    axios.get(`${API}/settings`).then(r => setSettings(r.data)).catch(() => setSettings({}));
  }, []);

  useEffect(() => {
    if (!settings) return;

    if (settings.site_title) document.title = settings.site_title;
    let metaDesc = document.querySelector('meta[name="description"]');
    if (!metaDesc) {
      metaDesc = document.createElement("meta"); metaDesc.name = "description";
      document.head.appendChild(metaDesc);
    }
    metaDesc.content = settings.site_description || "";

    // GA4
    if (settings.ga4_measurement_id) {
      if (!document.getElementById("ga4-src")) {
        const s = document.createElement("script"); s.async = true;
        s.id = "ga4-src";
        s.src = `https://www.googletagmanager.com/gtag/js?id=${settings.ga4_measurement_id}`;
        document.head.appendChild(s);
        const s2 = document.createElement("script"); s2.id = "ga4-init";
        s2.text = `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${settings.ga4_measurement_id}');`;
        document.head.appendChild(s2);
      }
    }

    // GTM
    if (settings.gtm_container_id && !document.getElementById("gtm-init")) {
      const s = document.createElement("script"); s.id = "gtm-init";
      s.text = `(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','${settings.gtm_container_id}');`;
      document.head.appendChild(s);
    }

    // Meta Pixel
    if (settings.meta_pixel_id && !document.getElementById("meta-pixel-init")) {
      const s = document.createElement("script"); s.id = "meta-pixel-init";
      s.text = `!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','${settings.meta_pixel_id}');fbq('track','PageView');`;
      document.head.appendChild(s);
    }

    const cleanupHead = injectHead("lp-custom-head", settings.custom_head_html);
    // custom body html
    if (settings.custom_body_html) {
      let el = document.getElementById("lp-custom-body");
      if (!el) { el = document.createElement("div"); el.id = "lp-custom-body"; document.body.appendChild(el); }
      el.innerHTML = settings.custom_body_html;
    }
    return () => cleanupHead();
  }, [settings]);

  return <SettingsCtx.Provider value={{ settings }}>{children}</SettingsCtx.Provider>;
}

export const useSiteSettings = () => useContext(SettingsCtx) || { settings: null };

export function useTrackPageView() {
  const loc = useLocation();
  useEffect(() => {
    trackEvent({ event_type: "page_view", path: loc.pathname + loc.search });
    // Also push to GA4/GTM if present
    if (window.gtag) window.gtag("event", "page_view", { page_path: loc.pathname });
    if (window.fbq) window.fbq("track", "PageView");
    // eslint-disable-next-line
  }, [loc.pathname, loc.search]);
}
