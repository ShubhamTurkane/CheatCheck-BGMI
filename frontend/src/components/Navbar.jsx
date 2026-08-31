import { Link, NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-border/90 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 md:px-6">
        <Link to="/" className="font-black tracking-tight text-xl">
          CheatCheck <span className="text-primary">BGMI</span>
        </Link>
        <nav className="flex items-center gap-5 text-sm font-semibold">
          <NavLink to="/" end className={({isActive}) => isActive ? "text-primary" : "text-ink-soft"}>
            Home
          </NavLink>
          <NavLink to="/analyze" className={({isActive}) => isActive ? "text-primary" : "text-ink-soft"}>
            Analyze
          </NavLink>
          <NavLink to="/admin" className={({isActive}) => isActive ? "text-primary" : "text-ink-soft"}>
            ML Admin
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
