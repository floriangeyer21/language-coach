import "./globals.css";

export const metadata = {
  title: "LanguageCoach",
  description: "AI language coach",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
