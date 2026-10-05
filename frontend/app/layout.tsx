import "./styles.css";
export const metadata = {
  title: "Independent Judge — Translation Comparison",
  description:
    "One source, two translations: quality indices, evidence and apparatus.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
