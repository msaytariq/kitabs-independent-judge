import "./styles.css";
export const metadata = {
  title: "Independent Judge | Editorial Workbench",
  description:
    "Measure expert-editor work against a shared publication standard.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
