import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import { LangProvider } from "@/lib/i18n";
import { CartProvider } from "@/lib/cart";
import { SiteSettingsProvider, useTrackPageView } from "@/lib/tracking";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import CookieBanner from "@/components/CookieBanner";
import CartDrawer from "@/components/CartDrawer";
import Home from "@/pages/Home";
import Catalog from "@/pages/Catalog";
import ProductDetail from "@/pages/ProductDetail";
import Compare from "@/pages/Compare";
import Checkout from "@/pages/Checkout";
import Support from "@/pages/Support";
import BundleBuilder from "@/pages/BundleBuilder";
import Family, { FamiliesIndex } from "@/pages/Family";
import { Transparency, Legal, Needs } from "@/pages/StaticPages";
import AdminApp from "@/admin/AdminApp";

function PublicShell() {
  useTrackPageView();
  const loc = useLocation();
  if (loc.pathname.startsWith("/admin")) return null;
  return (
    <>
      <Nav />
      <main className="min-h-screen">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/catalog" element={<Catalog />} />
          <Route path="/needs" element={<Needs />} />
          <Route path="/bundle" element={<BundleBuilder />} />
          <Route path="/families" element={<FamiliesIndex />} />
          <Route path="/family/:slug" element={<Family />} />
          <Route path="/product/:slug" element={<ProductDetail />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/support" element={<Support />} />
          <Route path="/transparency" element={<Transparency />} />
          <Route path="/legal/privacy" element={<Legal kind="privacy" />} />
          <Route path="/legal/terms" element={<Legal kind="terms" />} />
          <Route path="/legal/cookies" element={<Legal kind="cookies" />} />
          <Route path="/legal/withdrawal" element={<Legal kind="withdrawal" />} />
          <Route path="/legal/delivery" element={<Legal kind="delivery" />} />
          <Route path="/legal/refunds" element={<Legal kind="refunds" />} />
        </Routes>
      </main>
      <CartDrawer />
      <Footer />
    </>
  );
}

function Root() {
  const loc = useLocation();
  const isAdmin = loc.pathname.startsWith("/admin");
  return (
    <>
      {isAdmin ? (
        <Routes>
          <Route path="/admin/*" element={<AdminApp />} />
        </Routes>
      ) : (
        <PublicShell />
      )}
    </>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <SiteSettingsProvider>
          <LangProvider>
            <CartProvider>
              <Root />
              <CookieBanner />
              <Toaster theme="dark" position="bottom-right" toastOptions={{ style: { background: "#0B0B0D", color: "#fff", border: "1px solid rgba(255,255,255,0.1)" } }} />
            </CartProvider>
          </LangProvider>
        </SiteSettingsProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
