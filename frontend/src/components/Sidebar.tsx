'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navigation = [
  { name: 'Dashboard', href: '/' },
  { name: 'My Restaurant', href: '/my-restaurant' },
  { name: 'Competitors', href: '/competitors' },
  { name: 'Alerts', href: '/alerts' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-slate-900">
      <div className="flex flex-col flex-1">
        {/* Logo */}
        <div className="flex items-center h-16 px-6 border-b border-slate-800">
          <span className="text-xl font-bold text-white">Forkast CI</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`
                  flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                  ${isActive
                    ? 'bg-forkast-green-500 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }
                `}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800">
          <p className="text-xs text-slate-500">
            Competitive Intelligence
          </p>
        </div>
      </div>
    </aside>
  );
}
