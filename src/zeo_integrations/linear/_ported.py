"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/linear/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from zeo_integrations._http.runtime import HTTPException


class LinearClient:
    def __init__(self, transport):
        self._http = transport
        self.base_url = "https://api.linear.app/graphql"
        self.headers = {"Content-Type": "application/json"}

    def execute_query(self, query: str, variables: dict = None) -> dict:
        response = self._http.post(
            self.base_url,
            json={"query": query, "variables": variables or {}},
            headers=self.headers,
        )
        result = response.json()
        if "errors" in result:
            raise HTTPException(
                status_code=422, detail=f"GraphQL Errors: {str(result)}"
            )
        return result

    def list_issues(self, cursor: str | None = None, max_results: int = 50) -> dict:
        query = (
            "\n        query Issues($cursor: String, $first: Int!) {\n     "
            "       issues(\n                first: $first, \n             "
            "   after: $cursor,\n                orderBy: createdAt\n      "
            "      ) {\n                nodes {\n                    id \n  "
            "                  title \n                    description \n  "
            "                  identifier\n                    state { id "
            "name }\n                    priority\n                    assi"
            "gnee { id name email }\n                    creator { id name"
            " email }\n                    createdAt \n                    "
            "updatedAt\n                    labels { nodes { name } }\n    "
            "                project { id }\n                    team { id"
            " key }\n                }\n                pageInfo { hasNextP"
            "age endCursor }\n            }\n        }\n        "
        )
        return self.execute_query(query, {"cursor": cursor, "first": max_results})

    def search_issues(
        self, search_term: str, cursor: str | None = None, max_results: int = 50
    ) -> dict:
        query = (
            "\n        query SearchIssues($searchTerm: String!, $cursor: S"
            "tring, $first: Int!) {\n          issues(\n            first: "
            "$first\n            after: $cursor\n            orderBy: updat"
            "edAt\n            filter: {\n              or: [\n             "
            "   { title: { contains: $searchTerm } },\n                { d"
            "escription: { contains: $searchTerm } }\n              ]\n    "
            "        }\n          ) {\n            nodes {\n              id"
            "\n              title\n              description\n             "
            " identifier\n              state { id name }\n              pr"
            "iority\n              assignee { id name email }\n            "
            "  creator { id name email }\n              createdAt\n        "
            "      updatedAt\n              url\n            }\n            "
            "pageInfo {\n              hasNextPage\n              endCursor"
            "\n            }\n          }\n        }\n        "
        )
        return self.execute_query(
            query, {"searchTerm": search_term, "cursor": cursor, "first": max_results}
        )

    def filter_issues(
        self, graphql_filters: dict, cursor: str | None = None, max_results: int = 50
    ) -> dict:
        query = (
            "\n        query FilterIssues($filter: IssueFilter, $cursor: S"
            "tring, $first: Int!) {\n            issues(filter: $filter, f"
            "irst: $first, after: $cursor) {\n                nodes {\n    "
            "                id \n                    title \n             "
            "       description\n                    identifier\n          "
            "          state { id name }\n                    priority\n   "
            "                 assignee { id name email }\n                "
            "    creator { id name email }\n                    createdAt "
            "\n                    updatedAt\n                    labels { "
            "nodes { name } }\n                    project { id }\n        "
            "            team { id key }\n                }\n              "
            "  pageInfo { hasNextPage endCursor }\n            }\n        }"
            "\n        "
        )
        return self.execute_query(
            query, {"filter": graphql_filters, "cursor": cursor, "first": max_results}
        )

    def create_issue(self, input_data: dict) -> dict:
        query = (
            "\n        mutation CreateIssue($input: IssueCreateInput!) {\n "
            "           issueCreate(input: $input) {\n                issu"
            "e {\n                    id \n                    title \n     "
            "               description\n                    identifier\n  "
            "                  state { id name }\n                    prio"
            "rity\n                    assignee { id name email }\n        "
            "            creator { id name email }\n                    cr"
            "eatedAt \n                    updatedAt\n                    l"
            "abels { nodes { name } }\n                    project { id }\n"
            "                    team { id key }\n                }\n      "
            "      }\n        }\n        "
        )
        return self.execute_query(query, {"input": input_data})

    def update_issue(self, issue_id: str, input_data: dict) -> dict:
        query = (
            "\n        mutation UpdateIssue($id: String!, $input: IssueUpd"
            "ateInput!) {\n            issueUpdate(id: $id, input: $input)"
            " {\n                success\n                issue {\n         "
            "           id\n                    title\n                    "
            "description\n                    identifier\n                 "
            "   state { \n                        id \n                    "
            "    name \n                    }\n                    priority"
            "\n                    assignee { \n                        id "
            "\n                        name \n                        email"
            " \n                    }\n                    creator {\n      "
            "                  id\n                        name\n          "
            "              email\n                    }\n                  "
            "  createdAt\n                    updatedAt\n                  "
            "  labels { \n                        nodes { \n               "
            "             name \n                        } \n              "
            "      }\n                    project { \n                     "
            "   id \n                    }\n                    team { \n   "
            "                     id \n                        key \n      "
            "              }\n                }\n            }\n        }\n  "
            "      "
        )
        return self.execute_query(query, {"id": issue_id, "input": input_data})

    def create_comment(self, issue_id: str, body: str) -> dict:
        query = (
            "\n        mutation CreateComment($input: CommentCreateInput!)"
            " {\n            commentCreate(input: $input) {\n              "
            "  success\n                comment {\n                    id\n "
            "                   body\n                    user { id name e"
            "mail }\n                    createdAt\n                }\n     "
            "       }\n        }\n        "
        )
        return self.execute_query(query, {"input": {"issueId": issue_id, "body": body}})

    def list_projects(self, cursor: str | None = None, max_results: int = 50) -> dict:
        query = (
            "\n        query Projects($cursor: String, $first: Int!) {\n   "
            "         projects(first: $first, after: $cursor) {\n         "
            "       nodes {\n                    id name description\n     "
            "               state\n                    createdAt updatedAt"
            "\n                    lead { id name email }\n                "
            "}\n                pageInfo { hasNextPage endCursor }\n       "
            "     }\n        }\n        "
        )
        return self.execute_query(query, {"cursor": cursor, "first": max_results})

    def get_project(self, project_id: str) -> dict:
        query = (
            "\n        query Project($id: String!) {\n            project(i"
            "d: $id) {\n                id name description\n              "
            "  state\n                createdAt updatedAt\n                "
            "lead { id name email }\n                issues {\n            "
            "        nodes {\n                        id title state { nam"
            "e }\n                    }\n                }\n            }\n  "
            "      }\n        "
        )
        return self.execute_query(query, {"id": project_id})

    def list_users(self, cursor: str | None = None, max_results: int = 50) -> dict:
        query = (
            "\n        query Users($cursor: String, $first: Int!) {\n      "
            "      users(first: $first, after: $cursor) {\n               "
            " nodes {\n                    id\n                    name\n   "
            "                 email\n                }\n                pag"
            "eInfo { hasNextPage endCursor }\n            }\n        }\n    "
            "    "
        )
        return self.execute_query(query, {"cursor": cursor, "first": max_results})

    def list_teams(self, cursor: str | None = None, max_results: int = 50) -> dict:
        query = (
            "\n        query Teams($cursor: String, $first: Int!) {\n      "
            "      teams(first: $first, after: $cursor) {\n               "
            " nodes {\n                    id\n                    name\n   "
            "                 key\n                    description\n       "
            "         }\n                pageInfo { hasNextPage endCursor "
            "}\n            }\n        }\n        "
        )
        return self.execute_query(query, {"cursor": cursor, "first": max_results})

    def get_team(self, team_id: str) -> dict:
        query = (
            "\n        query Team($id: String!) {\n            team(id: $id"
            ") {\n                id\n                name\n                "
            "key\n                description\n            }\n        }\n    "
            "    "
        )
        return self.execute_query(query, {"id": team_id})

    def list_workflow_states(
        self, cursor: str | None = None, max_results: int = 50
    ) -> dict:
        query = (
            "\n        query WorkflowStates($cursor: String, $first: Int!)"
            " {\n            workflowStates(first: $first, after: $cursor)"
            " {\n                nodes {\n                    id\n          "
            "          name\n                    color\n                   "
            " type\n                    position\n                    team "
            "{ id key name }\n                }\n                pageInfo {"
            " hasNextPage endCursor }\n            }\n        }\n        "
        )
        return self.execute_query(query, {"cursor": cursor, "first": max_results})

    def list_labels(self, cursor: str | None = None, max_results: int = 100) -> dict:
        """List all labels in the Linear workspace"""
        query = (
            "\n        query Labels($cursor: String, $first: Int!) {\n     "
            "       issueLabels(\n                first: $first\n          "
            "      after: $cursor\n                orderBy: updatedAt\n    "
            "        ) {\n                nodes {\n                    id\n "
            "                   name\n                }\n                pa"
            "geInfo {\n                    hasNextPage\n                   "
            " endCursor\n                }\n            }\n        }\n       "
            " "
        )
        return self.execute_query(query, {"cursor": cursor, "first": max_results})
