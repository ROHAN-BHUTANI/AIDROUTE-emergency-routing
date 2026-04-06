"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  BarChart3,
  Route,
  Settings,
  ChevronLeft,
  Zap,
  Bell,
  HelpCircle,
} from "lucide-react"

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "#", active: true },
  { icon: BarChart3, label: "Analytics", href: "#" },
  { icon: Route, label: "Routes", href: "#" },
]

const bottomNavItems = [
  { icon: Bell, label: "Notifications", href: "#" },
  { icon: HelpCircle, label: "Help & Support", href: "#" },
  { icon: Settings, label: "Settings", href: "#" },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-dvh flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300",
        collapsed ? "w-16" : "w-72 sm:w-64"
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-sidebar-border px-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
          <Zap className="h-5 w-5 text-primary-foreground" />
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-sidebar-foreground">
              Emergency AI
            </span>
            <span className="text-xs text-muted-foreground">Response Optimizer</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-3">
        <div className="mb-2 px-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {!collapsed && "Main"}
        </div>
        {navItems.map((item) => (
          <a
            key={item.label}
            href={item.href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 hover:bg-sidebar-accent",
              item.active
                ? "bg-sidebar-accent text-sidebar-primary"
                : "text-sidebar-foreground/70 hover:text-sidebar-foreground"
            )}
          >
            <item.icon className={cn("h-5 w-5 shrink-0", item.active && "text-primary")} />
            {!collapsed && <span>{item.label}</span>}
          </a>
        ))}
      </nav>

      {/* Bottom Navigation */}
      <div className="border-t border-sidebar-border p-3">
        {bottomNavItems.map((item) => (
          <a
            key={item.label}
            href={item.href}
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-sidebar-foreground/70 transition-all duration-200 hover:bg-sidebar-accent hover:text-sidebar-foreground"
          >
            <item.icon className="h-5 w-5 shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </a>
        ))}
      </div>

      {/* Collapse Button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-card text-muted-foreground shadow-sm transition-transform hover:bg-accent hover:text-foreground"
      >
        <ChevronLeft
          className={cn(
            "h-4 w-4 transition-transform duration-300",
            collapsed && "rotate-180"
          )}
        />
      </button>
    </aside>
  )
}
