import { Outlet } from 'react-router-dom';
import Header from './Header';

function Dashboard(){
    return (
        <>
        <Header/>
        <Outlet />
        </>
    )
}

export default Dashboard; 