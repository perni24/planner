import { useState } from "react";
import { Outlet } from "react-router-dom";
import Header from "./Header";
import SideBar from "./SideBar";

function Dashboard() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <SideBar
          isOpen={isSidebarOpen}
          onToggle={() => setIsSidebarOpen((currentValue) => !currentValue)}
        />
        <main className="flex-1 min-w-0 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default Dashboard;
