"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const FEATURES = [
  {
    icon: "🧠",
    title: "Multi-Agent Swarms",
    desc: "Dispatch coordinated teams of specialized agents — planner, coder, QA, devops — that collaborate to build real software.",
  },
  {
    icon: "📡",
    title: "Real-Time Monitoring",
    desc: "Watch every agent in action. See what task each one is working on, their live logs, and tool calls as they happen.",
  },
  {
    icon: "🛡️",
    title: "Human-in-the-Loop",
    desc: "Intervene at any time. Send a direct message to any agent, redirect their work, or stop them when they drift off course.",
  },
  {
    icon: "🗂️",
    title: "Topology Control",
    desc: "Choose from built-in topologies (Coding Swarm, Software Delivery, Research) or customize which agents participate.",
  },
];

export default function LandingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [user, loading, router]);

  return (
    <div className="min-h-screen flex flex-col bg-base text-primary">
      {/* Nav */}
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <span className="text-lg font-semibold tracking-tight">
          <span className="text-accent">Dev</span>Forge
        </span>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm text-secondary hover:text-primary transition-colors">
            Sign in
          </Link>
          <Link
            href="/register"
            className="text-sm px-4 py-2 bg-accent hover:bg-accent-hover rounded-lg font-medium transition-colors"
          >
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-6 py-24 gap-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/30 bg-accent-dim text-accent text-xs font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          Powered by multi-agent swarms · Real-time intervention
        </div>

        <h1 className="text-5xl sm:text-6xl font-bold tracking-tight max-w-3xl leading-tight">
          Deploy a{" "}
          <span className="text-accent">swarm of AI agents</span>{" "}
          to build your software
        </h1>

        <p className="text-secondary text-lg max-w-xl leading-relaxed">
          Add your requirements to a notebook, point the swarm at a directory, and watch
          specialized agents collaborate in real time — while you stay in control.
        </p>

        <div className="flex items-center gap-4">
          <Link
            href="/register"
            className="px-6 py-3 bg-accent hover:bg-accent-hover rounded-xl font-semibold text-sm transition-colors shadow-lg shadow-accent/20"
          >
            Start building
          </Link>
          <Link
            href="/login"
            className="px-6 py-3 border border-border hover:border-border-light rounded-xl font-semibold text-sm text-secondary hover:text-primary transition-colors"
          >
            Sign in
          </Link>
        </div>
      </main>

      {/* Features */}
      <section className="px-6 pb-24 max-w-5xl mx-auto w-full">
        <p className="text-center text-secondary text-sm mb-10 uppercase tracking-widest font-medium">
          From requirements to running code — with you in command
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="bg-card border border-border rounded-xl p-5 flex flex-col gap-3 hover:border-border-light transition-colors"
            >
              <span className="text-2xl">{f.icon}</span>
              <h3 className="font-semibold text-sm">{f.title}</h3>
              <p className="text-secondary text-xs leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
