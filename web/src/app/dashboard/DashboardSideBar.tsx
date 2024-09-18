import { BasicClickable } from "@/components/BasicClickable";
import Link from "next/link";
import React from "react";
import { FaBrain } from "react-icons/fa";
import SideBarHeader from "./SideBarHeader";

export default function DashboardSideBar() {

    return (
        <div className="
                w-64
                flex
                bg-background-weak
                3xl:w-72
                border-r 
                border-border 
                flex 
                flex-col 
                h-lvh
                transition-transform">
            {/* Logo Section */}
            <div className="mx-4 my-6">
                <SideBarHeader />
            </div>
            {/* Navigation Links */}
        </div>
    )
}
