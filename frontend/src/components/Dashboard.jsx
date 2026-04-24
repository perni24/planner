import { Outlet } from "react-router-dom";
import Header from "./Header";
import SideBar from "./SideBar";

function Dashboard() {
  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <SideBar />
        <main className="flex-1 min-w-0 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default Dashboard;
