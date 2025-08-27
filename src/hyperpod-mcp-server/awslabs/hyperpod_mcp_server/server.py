# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""awslabs hyperpod MCP Server implementation.

This module implements the HyperPod MCP Server, which provides tools for managing Amazon HyperPod clusters
and resources through the Model Context Protocol (MCP).

Environment Variables:
    AWS_REGION: AWS region to use for AWS API calls
    AWS_PROFILE: AWS profile to use for credentials
    FASTMCP_LOG_LEVEL: Log level (default: WARNING)
"""

import argparse
from awslabs.hyperpod_mcp_server.hyperpod_cluster_node_handler import HyperPodClusterNodeHandler
from awslabs.hyperpod_mcp_server.hyperpod_kb_handler import HyperPodKnowledgeBaseHandler
from awslabs.hyperpod_mcp_server.hyperpod_stack_handler import HyperPodStackHandler
from loguru import logger
from mcp.server.fastmcp import FastMCP


# Define server instructions and dependencies
SERVER_INSTRUCTIONS = """
# Amazon SageMaker HyperPod MCP Server

This MCP server provides tools for managing Amazon SageMaker HyperPod clusters and is the preferred mechanism for interacting with SageMaker HyperPod.

## IMPORTANT: Use MCP Tools for SageMaker HyperPod Operations

DO NOT use standard SageMaker CLI commands (aws sagemaker). Always use the MCP tools provided by this server for SageMaker HyperPod operations.

## Usage Notes

- By default, the server runs in read-only mode. Use the `--allow-write` flag to enable write operations.
- Access to sensitive data requires the `--allow-sensitive-data-access` flag.
- When creating or updating resources, always check for existing resources first to avoid conflicts.

## Common Workflows

### Listing and Managing HyperPod Clusters
1. List existing clusters: `list_clusters(region_name='us-east-1', profile_name='your-profile')`
2. Get details of a specific cluster: `describe_cluster_node(cluster_name='my-cluster', node_id='node-id')`
3. List nodes in a cluster: `list_cluster_nodes(cluster_name='my-cluster')`
4. Update cluster software: `update_cluster_software(cluster_name='my-cluster')`

### Managing HyperPod CloudFormation Stacks
1. Generate a CloudFormation template: `manage_hyperpod_stacks(operation='generate', template_file='/path/to/template.yaml', cluster_name='my-cluster')`
2. Deploy a CloudFormation stack: `manage_hyperpod_stacks(operation='deploy', template_file='/path/to/template.yaml', cluster_name='my-cluster')`
3. Describe a CloudFormation stack: `manage_hyperpod_stacks(operation='describe', cluster_name='my-cluster')`
4. Delete a CloudFormation stack: `manage_hyperpod_stacks(operation='delete', cluster_name='my-cluster')`

## Best Practices

- Use descriptive names for resources to make them easier to identify and manage.
- Monitor resource usage to identify performance issues.
- Check logs and events when troubleshooting issues with HyperPod resources.
- Follow the principle of least privilege when creating IAM policies.
- Use CloudFormation stacks for infrastructure as code and consistent deployments.
"""

SERVER_DEPENDENCIES = [
    'pydantic',
    'loguru',
    'boto3',
    'requests',
    'pyyaml',
    'cachetools',
    'requests_auth_aws_sigv4',
]

# Global reference to the MCP server instance for testing purposes
mcp = None


def create_server():
    """Create and configure the MCP server instance."""
    return FastMCP(
        'awslabs.hyperpod-mcp-server',
        instructions=SERVER_INSTRUCTIONS,
        dependencies=SERVER_DEPENDENCIES,
    )


def main():
    """Run the MCP server with CLI argument support."""
    global mcp

    parser = argparse.ArgumentParser(
        description='An AWS Labs Model Context Protocol (MCP) server for SageMaker HyperPod'
    )
    parser.add_argument(
        '--allow-write',
        action=argparse.BooleanOptionalAction,
        default=False,
        help='Enable write access mode (allow mutating operations)',
    )
    parser.add_argument(
        '--allow-sensitive-data-access',
        action=argparse.BooleanOptionalAction,
        default=False,
        help='Enable sensitive data access (required for reading logs, events, and sensitive information)',
    )

    args = parser.parse_args()

    allow_write = args.allow_write
    allow_sensitive_data_access = args.allow_sensitive_data_access

    # Log startup mode
    mode_info = []
    if not allow_write:
        mode_info.append('read-only mode')
    if not allow_sensitive_data_access:
        mode_info.append('restricted sensitive data access mode')

    mode_str = ' in ' + ', '.join(mode_info) if mode_info else ''
    logger.info(f'Starting HyperPod MCP Server{mode_str}')

    # Create the MCP server instance
    mcp = create_server()

    # Initialize handlers - all tools are always registered, access control is handled within tools
    HyperPodClusterNodeHandler(mcp, allow_write, allow_sensitive_data_access)
    HyperPodStackHandler(mcp, allow_write)
    HyperPodKnowledgeBaseHandler(mcp)

    # Run server
    mcp.run()

    return mcp


if __name__ == '__main__':
    main()
