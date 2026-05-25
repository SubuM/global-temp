%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#1a1a24', 'edgeLabelBackground':'#1a1a1a', 'tertiaryColor': '#fff', 'primaryTextColor': '#fff', 'lineColor': '#8c8ca3'}}}%%
graph TD
    %% Define Nodes
    subuser(Public Internet\nUser)
    
    subgraph tailnet [Tailscale Secured Network Edge]
        ts_funnel(Tailscale Funnel\n<Secure Public Gateway>)
        ts_tunnel{{Secure Reverse Tunnel}}
    end

    subgraph ec2 [AWS EC2 Cloud Instance\n<Firewall Closed to Public Internet>]
        app_proxy(Tailscale Internal Proxy)
        
        subgraph docker [Docker Container Isolation]
            frontend[[Frontend Component\n<React Dashboard>]]
            backend[[Backend Component\n<FastAPI App Logic>]]
        end
    end

    subgraph data [Data Layer]
        db_live[(Live SQL Server\n<Azure / Remote>)]
        db_mock[(Synthetic Engine\n<Local Fallback>)]
    end

    %% Define Flows & Interactions
    subuser -- "1. Standard HTTPS Request" --> ts_funnel
    ts_funnel -- "2. Validates & Handshakes" --> ts_tunnel
    
    ts_tunnel -- "3. Egress-Only Secure Link\n<Bypasses AWS Firewall>" --> app_proxy
    app_proxy -- "4. Delivers Traffic" --> frontend
    
    frontend -- "5. Reverse Proxies API calls\n(/api)" --> backend
    
    backend -- "6a. Live Data Connection\n<Success Path>" --> db_live
    backend -. "6b. Automated Switchover\n<Error Path>" .-> db_mock
    
    backend -- "7. Returns JSON Data" --> frontend
    frontend -- "8. Secures & Serves UI" --> subuser

    %% Styling for Diagram Components
    classDef secure fill:#306,stroke:#4d4dff,stroke-width:2px,color:white,rx:5,ry:5;
    classDef app fill:#333,stroke:#666,stroke-width:1px,color:white;
    classDef aws fill:#FF9900,stroke:#FF9900,stroke-width:1px,color:black,rx:5,ry:5;
    classDef datafill fill:#006400,stroke:#666,stroke-width:1px,color:white;
    classDef userfill fill:#555,stroke:#fff,stroke-width:1px,color:white,rx:5,ry:5;

    class ts_funnel,ts_tunnel,app_proxy secure;
    class frontend,backend app;
    class ec2 aws;
    class db_live,db_mock datafill;
    class subuser userfill;

    linkStyle 0,1,8 stroke:#ff4b4b,stroke-width:2px; %% Red for Public Traffic
    linkStyle 2,3 stroke:#4d4dff,stroke-width:2px,stroke-dasharray: 5 5; %% Blue Dash for Secure Tunnel
    linkStyle default stroke:#8c8ca3,stroke-width:1.5px;


## Explanation of the Workflow:
This diagram visualizes how a public request is securely managed without ever exposing your AWS EC2 instance's ports to the public internet.

Public Entrance: An external user makes a standard HTTPS request to your public URL. This traffic is received by the Tailscale Funnel at the edge of the secure network.

Secure Handshake: The Funnel terminates the SSL connection (providing the padlock icon) and initiates a handshake with your server through a pre-established Secure Reverse Tunnel. This connection is initiated from inside the EC2 instance, bypassing the AWS incoming firewall rules entirely.

Local Delivery: The internal Tailscale Proxy on the EC2 instance receives the traffic and hands it off to the specific internal port where your Docker Frontend is listening.

Application Logic:

The Frontend (React) serves the static dashboard files.

API requests (/api) are automatically reverse-proxied within Docker to the Backend (FastAPI).

Resilient Data Flow:

The Backend attempts to connect to the live SQL Server.

If that connection fails for any reason (missing credentials, network outage), the backend gracefully and automatically switches to the local Synthetic Engine (Mock Data) to ensure the dashboard always loads.

Secure Response: The requested data is passed back up the chain and delivered securely to the user.