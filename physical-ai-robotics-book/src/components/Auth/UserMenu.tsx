/**
 * UserMenu Component
 * 
 * Displays user authentication state in the navbar.
 * Shows sign in/up buttons for guests, user menu for authenticated users.
 */

import React, { useState, useRef, useEffect } from "react";
import { authClient } from "../../lib/auth-client";
import "./UserMenu.css";

export function UserMenu() {
  const { data: session, isPending } = authClient.useSession();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    await authClient.signOut();
    window.location.href = "/";
  };

  if (isPending) {
    return (
      <div className="user-menu-loading">
        <div className="user-menu-spinner" />
      </div>
    );
  }

  if (!session?.user) {
    return (
      <div className="user-menu-guest">
        <a href="/auth/signin" className="user-menu-signin">
          Sign In
        </a>
        <a href="/auth/signup" className="user-menu-signup">
          Sign Up
        </a>
      </div>
    );
  }

  const user = session.user;
  const initials = user.name
    ? user.name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2)
    : user.email[0].toUpperCase();

  return (
    <div className="user-menu" ref={menuRef}>
      <button
        className="user-menu-trigger"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        {user.image ? (
          <img src={user.image} alt={user.name || "User"} className="user-menu-avatar" />
        ) : (
          <div className="user-menu-avatar-placeholder">{initials}</div>
        )}
      </button>

      {isOpen && (
        <div className="user-menu-dropdown">
          <div className="user-menu-header">
            <span className="user-menu-name">{user.name || "User"}</span>
            <span className="user-menu-email">{user.email}</span>
          </div>
          <div className="user-menu-divider" />
          <button className="user-menu-item user-menu-signout" onClick={handleSignOut}>
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}

export default UserMenu;
