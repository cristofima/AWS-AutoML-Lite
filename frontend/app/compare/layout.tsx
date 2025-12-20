import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Compare Models',
  description: 'Compare multiple training runs side-by-side',
};

export default function CompareLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
