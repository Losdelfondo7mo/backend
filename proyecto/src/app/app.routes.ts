import { Routes } from '@angular/router';
import { Dashboard } from './pages/dashboard/dashboard';
import { Login } from './auth/login/login';
import { Registro } from './auth/registro/registro';

export const routes: Routes = [
    {path: "login", component: Login },
    {path: "dasboard", component: Dashboard },
    {path: "registro", component:Registro},
    {path:"", redirectTo: "/login", pathMatch: "full"}
];
