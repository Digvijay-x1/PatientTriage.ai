import { PRODUCT, PROVIDER } from "../lib/provider";
import { useLanguage } from "../context/LanguageContext";

// Legal notice shown at the bottom of every dashboard tab: the provider's
// name and postal address, the release, and the CE marking.

function ProviderFooter() {
  const { t } = useLanguage();

  return (
    <footer
      aria-label={t("Legal notice")}
      className="border-t border-slate-200 bg-white"
    >
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-6 text-xs text-slate-600 sm:flex-row sm:items-start sm:justify-between sm:px-6">

        <div>
          <p className="font-semibold text-slate-800">
            {PRODUCT.name} {t("version")} {PRODUCT.version}
          </p>

          <p className="mt-1">
            {t("Provider")}: {PROVIDER.name}
          </p>

          <address className="mt-1 not-italic">
            {PROVIDER.street}, {PROVIDER.postcodeCity}, {t(PROVIDER.country)}
            <br />
            <a
              href={`mailto:${PROVIDER.email}`}
              className="text-blue-700 underline"
            >
              {PROVIDER.email}
            </a>
          </address>

          <p className="mt-1">
            {t("EU database registration")}: {PRODUCT.euDatabaseRegistration}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <img
            src="/ce-mark.svg"
            alt={t("CE marking")}
            className="h-6 w-auto"
          />

          <p className="max-w-56">
            {t("CE marked high-risk AI system under Regulation (EU) 2024/1689.")}
          </p>
        </div>

      </div>
    </footer>
  );
}

export default ProviderFooter;
