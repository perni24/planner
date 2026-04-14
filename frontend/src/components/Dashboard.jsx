import { Outlet } from "react-router-dom";
import Header from "./Header";
import SideBar from "./SideBar";

function Dashboard() {
  return (
    <>
      <Header />
      <div className="flex">
        <SideBar />
        <main>
          <Outlet />
        </main>
      </div>
    </>
  );
}

export default Dashboard;
