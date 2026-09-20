import './globals.css';
import type { ReactNode } from 'react';

export default function RootLayout({children}:{children:ReactNode}){
return <html lang="en">
  <head>
    <script type="text/javascript" src="https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
    <script dangerouslySetInnerHTML={{__html: `function googleTranslateElementInit() { new google.translate.TranslateElement({pageLanguage: 'en'}, 'google_translate_element'); }`}}></script>
  </head>
  <body>
    <div id="google_translate_element" style={{position: 'absolute', top: 10, left: 10, zIndex: 1000}}></div>
    {children}
  </body>
</html>
}
