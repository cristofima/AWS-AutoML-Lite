import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Configure Training",
};

export default function ConfigureLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
