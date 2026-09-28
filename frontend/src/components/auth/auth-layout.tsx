import type { ReactNode } from "react";

import { BrandMark } from "@/components/auth/brand-mark";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-dvh bg-background">
      <aside className="relative hidden w-[47%] shrink-0 overflow-hidden border-r border-slate-800 bg-[#101923] text-white lg:flex lg:flex-col">
        <div className="relative z-10 flex min-h-0 flex-1 flex-col justify-between p-10 xl:p-14">
          <BrandMark inverted />

          <div className="relative mx-auto my-12 w-full max-w-lg xl:my-16">
            <div className="mb-8">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                Evidence-led investigation
              </p>
              <h2 className="mt-5 max-w-md text-4xl font-medium leading-[1.15] tracking-[-0.04em] text-slate-50 xl:text-[2.75rem]">
                Better questions.
                <br />
                Defensible insights.
              </h2>
              <p className="mt-5 max-w-sm text-sm leading-7 text-slate-400">
                Turn questions about your data into structured findings,
                transparent evidence, and a professional analytical report.
              </p>
            </div>

            <svg
              viewBox="0 0 480 240"
              fill="none"
              className="w-full overflow-visible"
              aria-hidden="true"
            >
              <defs>
                <pattern
                  id="auth-grid"
                  width="32"
                  height="32"
                  patternUnits="userSpaceOnUse"
                >
                  <circle cx="1" cy="1" r="1" fill="#334155" />
                </pattern>
              </defs>

              <rect
                x="1"
                y="1"
                width="478"
                height="238"
                rx="12"
                fill="url(#auth-grid)"
                opacity="0.55"
              />

              <rect
                x="1"
                y="1"
                width="478"
                height="238"
                rx="12"
                stroke="#1E293B"
              />

              <path
                d="M94 185L173 133L242 158L321 75L399 48"
                stroke="#64748B"
                strokeWidth="1.5"
              />

              <path
                d="M173 133L204 63L321 75L352 169L242 158"
                stroke="#334155"
                strokeWidth="1.5"
                strokeDasharray="5 6"
              />

              <path
                d="M94 185L242 158L352 169L399 48"
                stroke="#334155"
                strokeWidth="1.5"
                strokeDasharray="5 6"
              />

              {[94, 173, 204, 242, 321, 352, 399].map(
                (x, index) => {
                  const y = [185, 133, 63, 158, 75, 169, 48][index];
                  const highlighted = index === 3 || index === 4;

                  return (
                    <g key={`${x}-${y}`}>
                      <rect
                        x={x - 4}
                        y={y - 4}
                        width="8"
                        height="8"
                        rx="2"
                        fill={
                          highlighted ? "#CBD5E1" : "#1E293B"
                        }
                        stroke={highlighted ? "#E2E8F0" : "#64748B"}
                      />
                    </g>
                  );
                },
              )}

              <path
                d="M39 207H441"
                stroke="#1E293B"
                strokeWidth="1"
              />

              <text
                x="39"
                y="224"
                fill="#64748B"
                fontSize="9"
                fontFamily="monospace"
                letterSpacing="1.5"
              >
                QUESTION
              </text>

              <text
                x="177"
                y="224"
                fill="#64748B"
                fontSize="9"
                fontFamily="monospace"
                letterSpacing="1.5"
              >
                EVIDENCE
              </text>

              <text
                x="320"
                y="224"
                fill="#94A3B8"
                fontSize="9"
                fontFamily="monospace"
                letterSpacing="1.5"
              >
                INSIGHT
              </text>
            </svg>

            <div className="mt-6 flex items-center gap-2 text-xs text-slate-500">
              <span className="size-1.5 rounded-full bg-slate-600" />
              Data in.
              <span className="size-1.5 rounded-full bg-slate-700" />
              Evidence out.
              <span className="size-1.5 rounded-full bg-slate-700" />
              Decisions informed.
            </div>
          </div>

          <p className="text-[11px] leading-5 text-slate-600">
            A focused workspace for analytical thinking.
          </p>
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 items-center justify-center px-6 py-10 sm:px-10 lg:px-12">
        <div className="w-full max-w-[400px]">
          <div className="mb-10 lg:hidden">
            <BrandMark />
          </div>

          {children}
        </div>
      </main>
    </div>
  );
}
