import { Link } from 'react-router-dom';

function Header() {
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo / Nome App */}
          <div className="flex-shrink-0 flex items-center">
            <Link to="/" className="text-3xl font-bold text-indigo-600 tracking-tight">
              Planner<span className="text-gray-900">App</span>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
