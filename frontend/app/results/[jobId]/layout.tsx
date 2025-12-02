import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Training Results",
};

export default function ResultsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
