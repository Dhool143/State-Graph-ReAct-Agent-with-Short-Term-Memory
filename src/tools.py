def query_service_metrics(service_name: str) -> dict[str, str | float]:
    return {
        "service_name": service_name,
        "error_rate_percent": 8.0 if service_name == "auth-service" else 3.0,
        

    } 
    
    
def scale_kubernetes_cluster(service_name: str, replica_count: int) -> str:
    return f"Simulated scaling: {service_name} now has {replica_count} replicas."
    
def check_billing_balance(account_id: str) -> dict[str, str | float]:
    return {
        "account_id": account_id,
        "balance_usd": 2500.0,
        

    }
    
def execute_wire_transfer(recipient_id: str, amount_usd: float) -> str:
    return f"Simulated wire transfer of ${amount_usd:,.2f} to {recipient_id}."