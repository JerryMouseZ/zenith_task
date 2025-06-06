import Link from 'next/link';
import { Home, Calendar, FolderKanban, BarChart3, Settings } from 'lucide-react'; // Icons

const navigationItems = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Calendar', href: '/calendar', icon: Calendar },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Monitoring', href: '/monitoring', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-50 dark:bg-gray-800 p-4 border-r border-gray-200 dark:border-gray-700">
      <div className="mb-8">
        {/* Logo or App Name can go here if different from Navbar */}
        <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">ZenithTask</h2>
      </div>
      <nav>
        <ul>
          {navigationItems.map((item) => (
            <li key={item.name} className="mb-2">
              <Link
                href={item.href}
                className="flex items-center p-2 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md"
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
