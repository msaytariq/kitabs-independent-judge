import "./styles.css";
export const metadata = {
  title: "Независимый судья — сравнение переводов",
  description:
    "Оригинал и два перевода: правки, обоснования и научный аппарат.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
