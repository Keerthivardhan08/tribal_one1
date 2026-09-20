import "./globals.css";
import type { ReactNode } from "react";
import Script from "next/script";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        {/* Google Website Translator widget — free, no API key needed */}
        <div
          id="google_translate_element"
          style={{ position: "fixed", top: 10, right: 10, zIndex: 2000 }}
        ></div>

        {/* Step 1: define the init function BEFORE the translate script loads */}
        <Script id="google-translate-init" strategy="afterInteractive">
          {`
            function googleTranslateElementInit() {
              new google.translate.TranslateElement(
                { pageLanguage: 'en', autoDisplay: false },
                'google_translate_element'
              );
            }
          `}
        </Script>

        {/* Step 2: now load the translate script, which calls the function above */}
        <Script
          src="https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"
          strategy="afterInteractive"
        />

        {children}
      </body>
    </html>
  );
}
