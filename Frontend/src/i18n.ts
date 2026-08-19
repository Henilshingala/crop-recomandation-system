import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import hi from "./locales/hi.json";
import gu from "./locales/gu.json";
import mr from "./locales/mr.json";
import pa from "./locales/pa.json";
import ta from "./locales/ta.json";
import te from "./locales/te.json";
import kn from "./locales/kn.json";
import bn from "./locales/bn.json";
import or_ from "./locales/or.json";
import as_ from "./locales/as.json";
import brx from "./locales/brx.json";
import doi from "./locales/doi.json";
import gom from "./locales/gom.json";
import ks from "./locales/ks.json";
import mai from "./locales/mai.json";
import ml from "./locales/ml.json";
import mni from "./locales/mni.json";
import ne from "./locales/ne.json";
import sa from "./locales/sa.json";
import sat from "./locales/sat.json";
import sd from "./locales/sd.json";
import ur from "./locales/ur.json";

const LANG_KEY = "crs_language";

const savedLang = (() => {
  try {
    return localStorage.getItem(LANG_KEY) || "en";
  } catch {
    return "en";
  }
})();

i18n.use(initReactI18next).init({
  resources: {
    en:  { translation: en },
    hi:  { translation: hi },
    gu:  { translation: gu },
    mr:  { translation: mr },
    pa:  { translation: pa },
    ta:  { translation: ta },
    te:  { translation: te },
    kn:  { translation: kn },
    bn:  { translation: bn },
    or:  { translation: or_ },
    as:  { translation: as_ },
    brx: { translation: brx },
    doi: { translation: doi },
    gom: { translation: gom },
    ks:  { translation: ks },
    mai: { translation: mai },
    ml:  { translation: ml },
    mni: { translation: mni },
    ne:  { translation: ne },
    sa:  { translation: sa },
    sat: { translation: sat },
    sd:  { translation: sd },
    ur:  { translation: ur },
  },
  lng: savedLang,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

// Persist language choice
i18n.on("languageChanged", (lng: string) => {
  try {
    localStorage.setItem(LANG_KEY, lng);
  } catch {
    // ignore
  }
});

export default i18n;
