"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

export default function DesignSystemPage() {
  return (
    <div className="container mx-auto py-10 px-4 space-y-10">
      <div>
        <h1 className="text-4xl font-bold tracking-tight">Design System</h1>
        <p className="text-zinc-500 mt-2">Essential components for Enterprise Knowledge Assistant.</p>
      </div>

      <Separator />

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Buttons</h2>
        <div className="flex flex-wrap gap-4">
          <Button>Default</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="destructive">Destructive</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="link">Link</Button>
          <Button onClick={() => toast.success("Action completed!")}>Show Toast</Button>
        </div>
      </section>

      <Separator />

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Inputs</h2>
        <div className="max-w-sm space-y-4">
          <Input placeholder="Email Address" />
          <Input type="password" placeholder="Password" />
          <Input disabled placeholder="Disabled input" />
        </div>
      </section>

      <Separator />

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Cards</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Document Analysis</CardTitle>
              <CardDescription>Status of the current ingestion process.</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-zinc-600">The document is being parsed and chunks are being generated.</p>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline">Cancel</Button>
              <Button>View Details</Button>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center gap-4">
              <Avatar>
                <AvatarImage src="https://github.com/shadcn.png" />
                <AvatarFallback>AI</AvatarFallback>
              </Avatar>
              <div>
                <CardTitle>Assistant</CardTitle>
                <CardDescription>RAG Engine v1.0</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm">I&apos;m ready to help you with your corporate knowledge base.</p>
            </CardContent>
          </Card>
        </div>
      </section>

      <Separator />

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Tabs</h2>
        <Tabs defaultValue="chat" className="w-[400px]">
          <TabsList>
            <TabsTrigger value="chat">Chat History</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
          </TabsList>
          <TabsContent value="chat" className="p-4 border rounded-md mt-2">
            <ScrollArea className="h-[100px]">
              <div className="space-y-2">
                <p className="text-sm p-2 bg-zinc-100 rounded">What is the annual leave policy?</p>
                <p className="text-sm p-2 bg-blue-50 border border-blue-100 rounded">According to the handbook...</p>
                <p className="text-sm p-2 bg-zinc-100 rounded">How do I reset my password?</p>
                <p className="text-sm p-2 bg-blue-50 border border-blue-100 rounded">You can reset it via...</p>
              </div>
            </ScrollArea>
          </TabsContent>
          <TabsContent value="documents" className="p-4 border rounded-md mt-2">
            <p className="text-sm text-zinc-500">No documents found.</p>
          </TabsContent>
        </Tabs>
      </section>
    </div>
  );
}
