import { Suspense } from 'react';
import NetworkGraphPage from './NetworkGraphPage';

export default function NetworkPage() {
  return (
    <Suspense fallback={<div className="flex-1 bg-obsidian-950" />}>
      <NetworkGraphPage />
    </Suspense>
  );
}
